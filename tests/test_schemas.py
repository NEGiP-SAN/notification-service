from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models import NotificationChannel, NotificationStatus
from app.schemas import NotificationCreate, NotificationResponse

# ============================================================
# NotificationCreate Tests
# ============================================================


def test_create_notification_with_valid_data():
    notification = NotificationCreate(
        recipient="test@user.com",
        channel=NotificationChannel.SMS,
        title="Welcome Message",
        body="Welcome to our application!",
        metadata_json={"user_id": 1},
    )

    assert notification.recipient == "test@user.com"
    assert notification.title == "Welcome Message"
    assert notification.channel == NotificationChannel.SMS
    assert notification.body == "Welcome to our application!"
    assert notification.metadata_json == {"user_id": 1}


def test_create_notification_accepts_null_metadata():
    notification = NotificationCreate(
        recipient="test@user.com",
        channel=NotificationChannel.SMS,
        title="Welcome Message",
        body="Welcome to our application!",
        metadata_json=None,
    )

    assert notification.metadata_json is None


def test_create_notification_uses_default_channel():
    notification = NotificationCreate(
        recipient="test@user.com",
        title="Welcome Message",
        body="Welcome to our application!",
    )

    assert notification.channel == NotificationChannel.IN_APP


@pytest.mark.parametrize(
    "field",
    ["recipient", "title", "body"],
)
def test_create_notification_rejects_missing_required_fields(
    field,
):
    data = {
        "recipient": "test@user.com",
        "title": "Welcome Message",
        "body": "Welcome to our app!",
    }

    data.pop(field)

    with pytest.raises(ValidationError) as exc:
        NotificationCreate(**data)

    error = exc.value.errors()[0]

    assert error.get("type") == "missing"
    assert error.get("loc") == (field,)


@pytest.mark.parametrize(
    # Pytest splits this string using the comma and
    # interprets it as two names: "field", "value"
    "field, value",
    [("recipient", ""), ("title", ""), ("body", "")],
)
def test_create_notification_rejects_empty_required_fields(
    field,
    value,
):
    data = {
        "recipient": "test@user.com",
        "title": "Welcome Message",
        "body": "Welcome to our app!",
    }

    data[field] = value

    with pytest.raises(ValidationError) as exc:
        NotificationCreate(**data)

    error = exc.value.errors()[0]

    assert error.get("type") == "string_too_short"
    assert error.get("loc") == (field,)


@pytest.mark.parametrize(
    ("field", "value"),
    [("recipient", "a" * 91), ("title", "a" * 151)],
)
def test_create_notification_rejects_fields_exceeding_max_length(
    field,
    value,
):
    data = {
        "recipient": "test@user.com",
        "title": "Welcome Message",
        "body": "Welcome to our app!",
    }

    data[field] = value

    with pytest.raises(ValidationError) as exc:
        NotificationCreate(**data)

    error = exc.value.errors()[0]

    assert error.get("type") == "string_too_long"
    assert error.get("loc") == (field,)


def test_create_notification_rejects_invalid_channel():
    with pytest.raises(ValidationError) as exc:
        NotificationCreate(
            recipient="test@user.com",
            channel="INVALID CHANNEL",
            title="Welcome Message",
            body="Welcome to our application!",
        )

    error = exc.value.errors()[0]

    assert error.get("loc") == ("channel",)


def test_create_notification_accepts_metadata_dict():
    notification = NotificationCreate(
        recipient="test@user.com",
        channel=NotificationChannel.SMS,
        title="Welcome Message",
        body="Welcome to our application!",
        metadata_json={
            "conversation_id": 1,
            "sender_id": 5,
        },
    )

    assert notification.metadata_json == {
        "conversation_id": 1,
        "sender_id": 5,
    }


def test_create_notification_rejects_list_as_metadata():
    with pytest.raises(ValidationError) as exc:
        NotificationCreate(
            recipient="test@user.com",
            channel=NotificationChannel.SMS,
            title="Welcome Message",
            body="Welcome to our application!",
            metadata_json=["invalid", "metadata"],
        )

    error = exc.value.errors()[0]

    assert error.get("loc") == ("metadata_json",)


# ============================================================
# NotificationResponse Tests
# ============================================================


def test_notification_response_with_valid_data():
    now = datetime.now(UTC)

    notification = NotificationResponse(
        id=1,
        recipient="test@user.com",
        channel=NotificationChannel.SMS,
        title="Welcome",
        body=" Welcome to our application!",
        status=list(NotificationStatus)[1],
        created_at=now,
        read_at=None,
    )

    assert notification.id == 1
    assert notification.recipient == "test@user.com"
    assert notification.created_at == now
    assert notification.status == list(NotificationStatus)[1]
    assert notification.read_at is None


@pytest.mark.parametrize(
    "field",
    ["id", "status", "created_at"],
)
def test_notification_response_requires_id_status_and_created_at(
    field,
):
    data = {
        "id": 1,
        "recipient": "test@user.com",
        "channel": NotificationChannel.SMS,
        "title": "Welcome",
        "body": " Welcome to our application!",
        "status": list(NotificationStatus)[1],
        "created_at": datetime.now(UTC),
        "read_at": None,
    }

    data.pop(field)

    with pytest.raises(ValidationError) as exc:
        NotificationResponse(**data)

    error = exc.value.errors()[0]

    assert error.get("type") == "missing"
    assert error.get("loc") == (field,)


def test_notification_response_accepts_read_at_datetime():
    now = datetime.now(UTC)
    read_at = now + timedelta(minutes=10)

    notification = NotificationResponse(
        id=1,
        recipient="test@user.com",
        channel=NotificationChannel.SMS,
        title="Welcome",
        body=" Welcome to our application!",
        status=list(NotificationStatus)[1],
        created_at=now,
        read_at=read_at,
    )

    assert notification.read_at == read_at


def test_notification_response_validates_status():
    with pytest.raises(ValidationError) as exc:
        NotificationResponse(
            id=1,
            recipient="test@user.com",
            channel=NotificationChannel.SMS,
            title="Welcome",
            body=" Welcome to our application!",
            status="INVALID STATUS",
            created_at=datetime.now(UTC),
            read_at=None,
        )

    error = exc.value.errors()[0]

    assert error.get("loc") == ("status",)


def test_notification_response_from_attribute():
    now = datetime.now(UTC)

    class NotificationModel:
        id = 1
        recipient = "user@example.com"
        title = "Welcome"
        channel = NotificationChannel.SMS
        body = "Welcome Message"
        metadata_json = {"user_id": 1}
        status = list(NotificationStatus)[0]
        created_at = now
        read_at = None

    notification = NotificationResponse.model_validate(
        NotificationModel(),
    )

    assert notification.id == 1
    assert notification.channel == NotificationChannel.SMS
    assert notification.body == "Welcome Message"
    assert notification.created_at == now
