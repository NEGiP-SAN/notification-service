from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status

from tests.helpers import (
    create_notification,
    make_notification_data,
)

# ============================================================
#  Create Notification Route Tests
# ============================================================


@pytest.mark.anyio
async def test_create_notification_success(client):
    notification = make_notification_data(
        recipient="test-user",
        title="Welcome Message",
    )

    response = await client.post(
        "/notifications",
        json=notification.model_dump(mode="json"),
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["recipient"] == "test-user"
    assert data["title"] == "Welcome Message"


@pytest.mark.anyio
async def test_create_notification_invalid_payload(client):
    response = await client.post(
        "/notifications",
        json={},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ============================================================
#  List Notifications Route Tests
# ============================================================


@pytest.mark.anyio
async def test_get_notification_success(client, db_session):
    notification = await create_notification(
        session=db_session,
        recipient="test-user",
        title="Test Notification",
    )

    notification_id = notification.id

    response = await client.get(
        f"/notifications/{notification_id}",
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == notification.id
    assert data["recipient"] == "test-user"
    assert data["title"] == "Test Notification"


@pytest.mark.anyio
async def test_get_notification_not_found(client):
    response = await client.get("/notifications/3")

    assert response.status_code == status.HTTP_404_NOT_FOUND

    data = response.json()

    assert data["detail"] == "Notification not found"


# ============================================================
#  List Notifications Route Tests
# ============================================================


@pytest.mark.anyio
async def test_list_notifications_success(client, db_session):
    _notification = await create_notification(
        session=db_session,
        recipient="test-user",
        title="Welcome Message",
    )

    response = await client.get(
        "/notifications",
        params={
            "recipient": "test-user",
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert len(data) == 1
    assert data[0]["recipient"] == "test-user"
    assert data[0]["title"] == "Welcome Message"


@pytest.mark.anyio
async def test_list_notification_filters_by_recipient(
    client,
    db_session,
):
    await create_notification(
        session=db_session,
        recipient="recipient-a",
        title="First Notification for A",
    )
    await create_notification(
        session=db_session,
        recipient="recipient-a",
        title="Second Notification for A",
    )
    await create_notification(
        session=db_session,
        recipient="recipient-b",
        title="Notification for B",
    )

    response = await client.get(
        "/notifications",
        params={
            "recipient": "recipient-a",
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert len(data) == 2

    titles = {notification["title"] for notification in data}

    assert titles == {
        "First Notification for A",
        "Second Notification for A",
    }


@pytest.mark.anyio
async def test_list_notification_sorts_newest_first(
    client,
    db_session,
):
    now = datetime.now(UTC)

    first = await create_notification(
        session=db_session,
        recipient="random-user",
        title="First Notification",
    )
    second = await create_notification(
        session=db_session,
        recipient="random-user",
        title="Second Notification",
    )
    third = await create_notification(
        session=db_session,
        recipient="random-user",
        title="Third Notification",
    )

    first.created_at = now
    second.created_at = now + timedelta(minutes=1)
    third.created_at = now + timedelta(minutes=2)

    # Sort notifications by creation time (newest first),
    # using the ID as a secondary sorting criterion.
    expected = sorted(
        [first, second, third],
        key=lambda notification: (
            notification.created_at,
            notification.id,
        ),
        reverse=True,
    )

    response = await client.get(
        "/notifications",
        params={
            "recipient": "random-user",
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    expected_ids = [notification.id for notification in expected]
    result_ids = [notification["id"] for notification in data]

    assert expected_ids == result_ids


@pytest.mark.anyio
async def test_list_notifications_empty_notification(client):
    response = await client.get(
        "/notifications",
        params={
            "recipient": "random-user",
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


@pytest.mark.anyio
async def test_list_notifications_missing_params(client):
    response = await client.get("/notifications")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.anyio
async def test_list_notifications_recipient_too_long(client):
    response = await client.get(
        "/notifications",
        params={
            "recipient": "a" * 91,
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.anyio
async def test_list_notifications_invalid_limit(client):
    response = await client.get(
        "/notifications",
        params={
            "recipient": "random-user",
            "limit": 100,
            "offset": 0,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.anyio
async def test_list_notifications_invalid_offset(client):
    response = await client.get(
        "/notifications",
        params={
            "recipient": "random-user",
            "limit": 10,
            "offset": -10,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ============================================================
#  Mark Notification as Read Route Tests
# ============================================================


@pytest.mark.anyio
async def test_mark_notification_as_read_success(client, db_session):
    notification = await create_notification(
        session=db_session,
        recipient="test-user",
        title="Random Title",
    )

    notification_id = notification.id

    assert notification.read_at is None

    response = await client.patch(
        f"/notifications/{notification_id}/read",
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == notification.id
    assert data["recipient"] == "test-user"
    assert data["title"] == "Random Title"
    assert data["read_at"] is not None


@pytest.mark.anyio
async def test_mark_notification_as_read_not_found(client):

    response = await client.patch("/notifications/3/read")

    assert response.status_code == status.HTTP_404_NOT_FOUND

    data = response.json()

    assert data["detail"] == "Notification not found"
