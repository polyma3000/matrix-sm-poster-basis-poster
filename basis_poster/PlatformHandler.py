import logging
from typing import Type

import functions
from Message import Message


class PlatformHandler:
    def __init__(self, base_message_class: Type[Message], db_filename: str, platform_name: str,
                 add_platform_connection_callable: callable):
        logging.getLogger().debug('Started..')
        self.MESSAGES_TO_SEND = {}
        self.SENT_MESSAGES = []
        self.db_filename = db_filename
        self.base_message_class = base_message_class
        self.platform_name = platform_name
        self.PLATFORM_CONNECTIONS = {}
        self.add_platform_connection_callable = add_platform_connection_callable
        logging.getLogger().debug('Finished..')

    async def get_messages_from_db(self):
        logging.getLogger().debug('Started..')
        sql = """SELECT messages_to_platforms.id, messages_id, matrix_connection_name, matrix_room_id, 
        body, pictures_ids, json_data
        FROM messages INNER JOIN messages_to_platforms ON messages_to_platforms.messages_id = messages.id
        WHERE messages_to_platforms.platform_name = ? AND messages_to_platforms.sent = ?"""

        messages_raw = await functions.get_from_db(self.db_filename, sql, (self.platform_name, 0))
        for message in messages_raw:
            if message[0] not in self.MESSAGES_TO_SEND and message[0] not in self.SENT_MESSAGES:
                msg = self.base_message_class(message)
                if msg.details[f"{self.platform_name}_connection_name"] in self.PLATFORM_CONNECTIONS:
                    self.MESSAGES_TO_SEND[msg.id] = msg
        logging.getLogger().debug('Finished..')

    async def send_messages_to_platform(self):
        logging.getLogger().debug('Started..')
        for message in self.MESSAGES_TO_SEND:
            if message.details[f"{self.platform_name}_connection_name"] in self.PLATFORM_CONNECTIONS:
                if message.send_to_platform_handler(self.PLATFORM_CONNECTIONS[f"{self.platform_name}_connection_name"]):
                    del(self.MESSAGES_TO_SEND[message.id])
                    self.SENT_MESSAGES.append(message.id)
        logging.getLogger().debug('Finished..')

    async def update_messages_in_db(self):
        logging.getLogger().debug('Started..')
        update_data = []
        for messages_to_platform_id in self.SENT_MESSAGES:
            update_data.append((1, messages_to_platform_id))

        sql = """UPDATE messages_to_platforms SET sent = ? WHERE id = ?"""
        if not update_data:
            return
        await functions.send_sql(self.db_filename, sql, update_data)

        for single_update_data in update_data:
            self.SENT_MESSAGES.remove(single_update_data[1])
        logging.getLogger().debug('Finished..')

    async def reload_connections(self):
        logging.getLogger().debug('Started..')
        await functions.check_for_db_and_connections_files()
        connections = functions.load_connections_from_file()
        for platform_connection_name in self.PLATFORM_CONNECTIONS:
            if platform_connection_name not in connections[f"{self.platform_name}_connections"]:
                del (self.PLATFORM_CONNECTIONS[platform_connection_name])
        self.init_mastodon_connections(connections)
        logging.getLogger().debug('Finished..')

    def init_mastodon_connections(self, connections):
        logging.getLogger().debug('Started..')
        for platform_connection_name in connections[f"{self.platform_name}_connections"]:
            if platform_connection_name not in self.PLATFORM_CONNECTIONS:
                self.PLATFORM_CONNECTIONS[platform_connection_name] = self.add_platform_connection_callable(
                    connections[f"{self.platform_name}_connections"][platform_connection_name]
                )
                logging.getLogger().debug(f"Added initializing connection for {platform_connection_name}")
        logging.getLogger().debug('Finished..')



