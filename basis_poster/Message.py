from __future__ import annotations

import logging
import json

from basis_poster import functions


class Message:
    def __init__(self, pictures_dir: str, max_text_length: int, row_data: tuple):
        (self.id, self.messages_id, self.matrix_connection_name, self.matrix_room_id,
            self.body, self.pictures_ids, json_data) = row_data

        if max_text_length <= 0:
            self.posts = [self.body]
        else:
            self.posts = functions.split_text_for_platform(self.body, max_text_length)
        self.pictures_names = functions.load_pictures_names(pictures_dir, self.pictures_ids)
        self.details = json.loads(json_data)
        self.errors = self.get_errors()
        self.sending = False

    async def send_to_platform_handler(self, platform_connection: object):
        logging.getLogger().debug('Started..')
        if self.sending:
            return
        self.sending = True

        successful = False

        try:
            await self.send_to_platform(platform_connection)
        except self.errors as error:
            self.sending = False
            logging.getLogger().exception(f"Sending of message {self.posts} failed due to Connection error..")
            pass
        else:
            self.sending = False
            successful = True
        logging.getLogger().debug('Finished..')
        return successful

    async def send_to_platform(self, platform_connection: object):
        return

    @classmethod
    def get_errors(cls):
        return TimeoutError
