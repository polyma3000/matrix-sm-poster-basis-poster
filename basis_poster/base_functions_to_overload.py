from basis_poster.Connection import Connection
from basis_poster.models import MessageModel, MessageReturnModel, MessagePhotoReturnModel


async def get_connection_object(connection_details: dict) -> object:
    return object


async def send_message(connection: Connection, message: MessageModel) -> MessageReturnModel:
    return MessageReturnModel(message_body=message.message_body,
                              message_details=message.message_details,
                              message_for_next_message={},
                              message_previous_message={})


async def send_message_with_photo(connection: Connection, message: MessageModel,
                                  photo_name: str) -> MessagePhotoReturnModel:
    return MessagePhotoReturnModel(message_body=message.message_body,
                                   message_details=message.message_details, message_for_next_message={},
                                   message_previous_message={}, message_photo_name=photo_name)
