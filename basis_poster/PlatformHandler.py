import logging
import asyncio
from typing import Type

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import functions
from Message import Message


class PlatformHandler:
    def __init__(self, base_message_class: Type[Message], platform_name: str, max_text_length: int,
                 db_filename: str = "data/shared_messages.db", connections_filename: str = "data/connections.yaml",
                 pictures_directory_name: str = "data/pictures"):
        self.max_text_length = max_text_length
        logging.getLogger().debug('Started..')
        self.MESSAGES_TO_SEND = {}
        self.SENT_MESSAGES = []
        self.db_filename = db_filename
        self.connections_filename = connections_filename
        self.pictures_directory_name = pictures_directory_name
        self.base_message_class = base_message_class
        self.platform_name = platform_name
        self.PLATFORM_CONNECTIONS = {}

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.runner, 'interval', minutes=1)

        self.reload_connections()

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
                msg = self.base_message_class(self.pictures_directory_name, self.max_text_length, message)
                if msg.details[f"{self.platform_name}_connection_name"] in self.PLATFORM_CONNECTIONS:
                    self.MESSAGES_TO_SEND[msg.id] = msg
        logging.getLogger().debug('Finished..')

    async def send_messages_to_platform(self):
        logging.getLogger().debug('Started..')
        task_list = []
        for message in self.MESSAGES_TO_SEND:
            if message.details[f"{self.platform_name}_connection_name"] in self.PLATFORM_CONNECTIONS:
                task_list.append(self.send_message_to_platform(message))
        await asyncio.gather(*task_list)
        logging.getLogger().debug('Finished..')

    async def send_message_to_platform(self, message: Message):
        if await message.send_to_platform_handler(self.PLATFORM_CONNECTIONS[f"{self.platform_name}_connection_name"]):
            del (self.MESSAGES_TO_SEND[message.id])
            self.SENT_MESSAGES.append(message.id)

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
        await functions.check_for_db_and_connections_files(
            files=[self.db_filename, self.connections_filename],
            dirs=[self.pictures_directory_name])
        connections = functions.load_connections_from_file(self.connections_filename)
        for platform_connection_name in self.PLATFORM_CONNECTIONS:
            if platform_connection_name not in connections[f"{self.platform_name}_connections"]:
                del (self.PLATFORM_CONNECTIONS[platform_connection_name])
        self.init_platform_connections(connections)
        logging.getLogger().debug('Finished..')

    def init_platform_connections(self, connections):
        logging.getLogger().debug('Started..')
        for platform_connection_name in connections[f"{self.platform_name}_connections"]:
            if platform_connection_name not in self.PLATFORM_CONNECTIONS:
                self.PLATFORM_CONNECTIONS[platform_connection_name] = self.add_platform_connection(
                    platform_connection_name,
                    connections[f"{self.platform_name}_connections"][platform_connection_name]
                )
                logging.getLogger().debug(f"Added initializing connection for {platform_connection_name}")
        logging.getLogger().debug('Finished..')

    async def start(self):
        logging.getLogger().debug('Started..')

        await self.runner()
        self.scheduler.start()

        await asyncio.Event().wait()
        logging.getLogger().debug('Finished..')

    async def runner(self):
        logging.getLogger().debug('Started..')
        await asyncio.gather(self.reload_connections(), self.get_messages_from_db())

        await self.send_messages_to_platform()

        await self.update_messages_in_db()
        logging.getLogger().debug('Finished..')

    def run(self):
        asyncio.run(self.start())

    @staticmethod
    def add_platform_connection(platform_connection_name: str, platform_connection: dict):
        return {platform_connection_name: platform_connection}
