from datetime import UTC, datetime, timedelta

import pytest

from app.models import (
    NotificationStatus,
)
from app.repository import NotificationRepository
from tests.helpers import (
    create_notification,
    make_notification_data,
)

# ============================================================
#  Create Notification Tests
# ============================================================


@pytest.mark.anyio
async def test_create_notification_success(
    db_session,
):
    repo = NotificationRepository(db_session)

    data = make_notification_data()

    notification = await repo.create(data=data)

    assert notification.id is not None
    assert notification.recipient == data.recipient
    assert notification.channel == data.channel
    assert notification.title == data.title
    assert notification.body == data.body


@pytest.mark.anyio
async def test_create_notification_sets_pending_status(
    db_session,
):
    repo = NotificationRepository(db_session)

    data = make_notification_data()

    notification = await repo.create(data=data)

    assert notification.status == NotificationStatus.PENDING


@pytest.mark.anyio
async def test_create_notification_with_metadata(
    db_session,
):
    repo = NotificationRepository(db_session)

    data = make_notification_data(
        metadata_json={"user_id": 1},
    )

    notification = await repo.create(data=data)

    assert notification.metadata_json == data.metadata_json


# ============================================================
#  Get Notification by ID Tests
# ============================================================


@pytest.mark.anyio
async def test_get_notification_by_id_success(
    db_session,
):
    repo = NotificationRepository(db_session)

    notification = await create_notification(db_session)

    db_notification = await repo.get_by_id(notification.id)

    assert db_notification is not None
    assert db_notification.id == notification.id


@pytest.mark.anyio
async def test_get_notification_by_id_for_when_missing(
    db_session,
):
    repo = NotificationRepository(db_session)

    notification = await repo.get_by_id(3)

    assert notification is None


# ============================================================
#  List Notification for Recipient Tests
# ============================================================


@pytest.mark.anyio
async def test_list_for_recipient_sorts_newest_first(
    db_session,
):
    repo = NotificationRepository(db_session)

    time1 = datetime.now(UTC)
    time2 = time1 + timedelta(minutes=1)
    time3 = time2 + timedelta(minutes=1)

    notification1 = await create_notification(
        session=db_session,
        recipient="test-user",
        title="First Notification",
        created_at=time1,
    )
    notification2 = await create_notification(
        session=db_session,
        recipient="test-user",
        title="First Notification",
        created_at=time2,
    )
    notification3 = await create_notification(
        session=db_session,
        recipient="test-user",
        title="First Notification",
        created_at=time3,
    )

    notifications = await repo.list_for_recipient(
        recipient="test-user",
        limit=10,
        offset=0,
    )

    assert len(notifications) == 3
    assert notifications[0] == notification3
    assert notifications[1] == notification2
    assert notifications[2] == notification1


@pytest.mark.anyio
async def test_list_for_recipient_filters_by_recipient(
    db_session,
):
    repo = NotificationRepository(db_session)
    notification1 = await create_notification(
        session=db_session,
        recipient="test-user",
        title="First Notification",
    )
    notification2 = await create_notification(
        session=db_session,
        recipient="test-user",
        title="First Notification",
    )
    await create_notification(
        session=db_session,
        recipient="test-user2",
        title="First Notification",
    )

    notifications = await repo.list_for_recipient(
        recipient="test-user",
        limit=10,
        offset=0,
    )

    assert len(notifications) == 2
    assert notification1 in notifications
    assert notification2 in notifications


@pytest.mark.anyio
async def test_list_for_recipient_with_no_notifications(
    db_session,
):
    repo = NotificationRepository(db_session)

    notifications = await repo.list_for_recipient(
        recipient="random-user",
        limit=10,
        offset=0,
    )

    assert notifications == []


@pytest.mark.anyio
async def test_list_for_recipient_respects_limit(
    db_session,
):
    repo = NotificationRepository(db_session)

    for i in range(11):
        await create_notification(
            db_session,
            recipient="test-user",
            title=f"Notification {i}",
        )

    notifications1 = await repo.list_for_recipient(
        recipient="test-user",
        limit=10,
        offset=0,
    )

    assert len(notifications1) == 10


@pytest.mark.anyio
async def test_list_for_recipient_respects_offset(
    db_session,
):
    repo = NotificationRepository(db_session)

    for i in range(13):
        await create_notification(
            db_session,
            recipient="test-user",
            title=f"Notification {i}",
        )

    notifications1 = await repo.list_for_recipient(
        recipient="test-user",
        limit=10,
        offset=0,
    )
    notifications2 = await repo.list_for_recipient(
        recipient="test-user",
        limit=10,
        offset=10,
    )

    first_id = {item.id for item in notifications1}
    second_id = {item.id for item in notifications2}

    assert len(notifications1) == 10
    assert len(notifications2) == 3
    assert first_id.isdisjoint(second_id)


@pytest.mark.anyio
async def test_list_for_recipient_respects_limit_and_offset(
    db_session,
):
    repo = NotificationRepository(db_session)

    for i in range(5):
        await create_notification(
            db_session,
            recipient="test-user",
            title=f"Notification {i}",
        )

    all_notifications = await repo.list_for_recipient(
        recipient="test-user",
        limit=5,
        offset=0,
    )

    page = await repo.list_for_recipient(
        recipient="test-user",
        limit=2,
        offset=1,
    )

    assert page == all_notifications[1:3]


@pytest.mark.anyio
async def test_list_for_recipient_uses_id_as_tiebreaker(
    db_session,
):
    repo = NotificationRepository(db_session)

    time1 = datetime.now(UTC)
    time2 = datetime.now(UTC) + timedelta(minutes=3)

    notification1 = await create_notification(
        db_session,
        recipient="test-user",
        created_at=time2,
    )
    notification2 = await create_notification(
        db_session,
        recipient="test-user",
        created_at=time2,
    )
    _notification3 = await create_notification(
        db_session,
        recipient="test-user",
        created_at=time1,
    )

    notifications = await repo.list_for_recipient(
        recipient="test-user",
        limit=10,
        offset=0,
    )

    assert len(notifications) == 3

    # When created_at values are equal
    # notifications are ordered by ID (desc)
    assert notification2.id > notification1.id
    assert notifications[0] == notification2
    assert notifications[1] == notification1


# ============================================================
#  Notifications Marked as Read Tests
# ============================================================


@pytest.mark.anyio
async def test_mark_as_read_sets_read_at(db_session):
    repo = NotificationRepository(db_session)

    notification = await create_notification(
        db_session,
        recipient="test-user",
    )

    assert notification.read_at is None

    notification = await repo.mark_as_read(notification)

    assert notification.read_at is not None
    assert notification.read_at.tzinfo is not None
    assert notification.read_at.utcoffset() == timedelta(0)


@pytest.mark.anyio
async def test_mark_as_read_preserves_existing_timestamp(
    db_session,
):
    repo = NotificationRepository(db_session)

    time = datetime.now(UTC) - timedelta(minutes=5)

    notification = await create_notification(
        db_session,
        recipient="test-user",
        read_at=time,
    )

    new_notification = await repo.mark_as_read(notification)

    assert notification.read_at == new_notification.read_at
    assert new_notification.read_at == time


@pytest.mark.anyio
async def test_mark_as_read_does_not_change_existing_timestamp(
    db_session,
):
    repo = NotificationRepository(db_session)
    notification = await create_notification(
        db_session,
        recipient="test-user",
    )

    await repo.mark_as_read(notification)
    original_read_at = notification.read_at

    await repo.mark_as_read(notification)

    assert notification.read_at == original_read_at
