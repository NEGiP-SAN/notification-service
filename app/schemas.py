from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models import (
    NotificationChannel,
    NotificationStatus,
)


class NotificationBase(BaseModel):
    recipient: str = Field(
        min_length=1,
        max_length=90,
    )
    title: str = Field(
        min_length=1,
        max_length=150,
    )
    channel: NotificationChannel = NotificationChannel.IN_APP
    body: str = Field(min_length=1)
    metadata_json: dict | None = None


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: int
    status: NotificationStatus
    created_at: datetime
    read_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )
