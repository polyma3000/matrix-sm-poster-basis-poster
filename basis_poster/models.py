from __future__ import annotations

from pydantic import BaseModel


class MessageModel(BaseModel):
    message_body: str
    message_details: dict
    message_previous_message: dict | None = None


class MessageReturnModel(MessageModel):
    message_previous_message: dict
    message_for_next_message: dict


class MessagePhotoReturnModel(MessageReturnModel):
    message_photo_name: str


class ConnectionInputModel(BaseModel):
    connection_name: str
    connection_settings: dict | None = None
    connection_details: dict


class ConnectionModel(ConnectionInputModel):
    connection_uuid: str

