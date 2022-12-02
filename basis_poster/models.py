from typing import Optional

from pydantic import BaseModel


class MessageModel(BaseModel):
    message_body: str
    message_details: dict
    message_previous_message: Optional[dict] = None


class MessageReturnModel(MessageModel):
    message_for_next_message: dict


class MessagePhotoReturnModel(MessageReturnModel):
    message_photo_name: str


class ConnectionInputModel(BaseModel):
    connection_name: str
    connection_settings: Optional[dict] = None
    connection_details: dict


class ConnectionModel(ConnectionInputModel):
    connection_uuid: str

