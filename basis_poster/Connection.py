import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime

from fastapi import HTTPException

from basis_poster.models import MessageModel, ConnectionInputModel, ConnectionModel


async def base_overload_function(*args):
    return args


class Connection:
    connections = {}
    connections_name_to_uuids = {}
    connection_settings = {
        'connection_databases_directory': os.environ.get('connection_database'.upper(),
                                                         'data/local_data/databases'),
        'connection_pictures_directory': os.environ.get('connection_pictures_directory'.upper(),
                                                        'data/shared_data/pictures'),
        'connection_max_text_length': int(os.environ.get('connection_max_text_length'.upper(), '500')),
        'connection_quota_amount': int(os.environ.get('connection_quota_amount'.upper(), '300')),
        'connection_quota_time_amount': int(os.environ.get('connection_quota_time_amount'.upper(), '5')),
        'connection_quota_time_unit': os.environ.get('connection_quota_time_unit'.upper(), 'minutes'),
        'connection_platform_name': os.environ.get('connection_platform_name'.upper(), 'matrix'),
    }

    connection_callables = {
        'connection_object_creator': base_overload_function,
        'connection_send_message': base_overload_function,
        'connection_send_message_with_photo': base_overload_function
    }

    connection_mandatory_keys_for_connection_details = []
    connection_mandatory_keys_for_message_details = []

    gateway_errors = TimeoutError

    def __init__(self, connection_data: ConnectionInputModel, connection_uuid: str):
        logging.getLogger().debug('Started..')

        for mandatory_key in self.connection_mandatory_keys_for_connection_details:
            if mandatory_key not in connection_data.connection_details:
                raise HTTPException(status_code=422,
                                    detail=f"Mandatory Key '{mandatory_key}' not found in connection_details")

        self.connection_uuid = connection_uuid
        self.connection_name = connection_data.connection_name
        if connection_data.connection_details:
            self.connection_details = connection_data.connection_details
        else:
            self.connection_details = {}

        if connection_data.connection_settings:
            for settings_key in connection_data.connection_settings:
                self.connection_settings[settings_key] = connection_data.connection_settings[settings_key]

        self.connection_object = self.connection_callables['connection_object_creator'](
            connection_data.connection_details)
        self.connection_db_filename = f"{self.connection_settings['connection_databases_directory']}/" \
                                      f"{self.connection_uuid}.db "

        self.connection_settings['connection_quota_seconds'] = self.connection_settings['connection_quota_time_amount']
        self.connection_settings['connection_quota_seconds'] *= self.get_seconds(
            self.connection_settings['connection_quota_time_unit'])

        self.create_database()

        Connection.connections[connection_uuid] = self
        Connection.connections_name_to_uuids[connection_data.connection_name] = connection_uuid

        logging.getLogger().debug('Finished..')

    @classmethod
    def check_directories(cls):
        while True:
            if (os.path.isdir(cls.connection_settings['connection_databases_directory']) and
                    os.path.isdir(cls.connection_settings['connection_pictures_directory'])):
                return
            logging.getLogger().info(f"Not all necessary files or directories in data are yet existent. Retrying in 10 "
                                     f"seconds.")
            time.sleep(10)

    @classmethod
    def create_connection(cls, connection_data: ConnectionInputModel):
        if connection_data.connection_name in cls.connections_name_to_uuids:
            return cls.connections[cls.connections_name_to_uuids[connection_data.connection_name]]
        else:
            uuid_str = str(uuid.uuid4())
            while uuid_str in cls.connections:
                uuid_str = str(uuid.uuid4())

            return cls(connection_data, uuid_str)

    @staticmethod
    def get_seconds(time_unit: str) -> int:
        mapping = {
            'second': 1,
            'seconds': 1,
            'minute': 60,
            'minutes': 60,
            'hour': 3600,
            'hours': 3600,
            'day': 3600*24,
            'days': 3600*24
        }
        time_unit = time_unit.lower()
        if time_unit in mapping:
            return mapping[time_unit]
        return -1

    async def load_file_path(self, file_name: str) -> str:
        for path, subdirectories, files in os.walk(self.connection_settings['connection_pictures_directory']):
            for name in files:
                if name.find(file_name) > -1:
                    return os.path.join(path, name)
        return ""

    def get_connection_model(self):
        return ConnectionModel(
            connection_name=self.connection_name,
            connection_details=dict(self.connection_details),
            connection_settings=dict(self.connection_settings),
            connection_uuid=self.connection_uuid
        )

    def create_database(self):
        logging.getLogger().debug('Started..')
        db_connection = sqlite3.connect(self.connection_db_filename, timeout=30)
        cur = db_connection.cursor()

        cur.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER NOT NULL PRIMARY KEY,
            started_datetime DATETIME,
            finished_datetime DATETIME DEFAULT NULL
            );""")
        db_connection.commit()

        cur.execute("""PRAGMA journal_mode = WAL;""")
        db_connection.commit()

        db_connection.close()
        logging.getLogger().debug('Finished..')

    async def check_quota_and_insert(self):
        logging.getLogger().debug('Started..')
        db_connection = sqlite3.connect(self.connection_db_filename, timeout=30)
        cur = db_connection.cursor()

        sql = """INSERT INTO messages (started_datetime)
            SELECT :now
            FROM (SELECT COUNT(started_datetime) AS messages_in_timeframe
                    FROM messages
                    WHERE (:now - finished_datetime) * 86400 <= :diff_seconds OR finished_datetime IS NULL
                ) AS messages_search
            WHERE COALESCE(messages_search.messages_in_timeframe, -1) < :max_quota OR :max_quota < 0"""
        now = datetime.now()

        cur.execute(sql, {
            'now': now.strftime("%Y-%m-%d %H:%M:%S"),
            'diff_seconds': self.connection_settings['connection_quota_seconds'],
            'max_quota': self.connection_settings['connection_quota_amount']
        })

        last_id = cur.lastrowid
        row_count = cur.rowcount
        db_connection.commit()
        db_connection.close()
        logging.getLogger().debug('Finished..')

        return row_count > 0, last_id

    async def update_message_in_db(self, message_id):
        logging.getLogger().debug('Started..')
        db_connection = sqlite3.connect(self.connection_db_filename, timeout=30)
        cur = db_connection.cursor()

        sql = """UPDATE messages SET finished_datetime=:finished_datetime WHERE id=:message_id"""
        now = datetime.now()

        cur.execute(sql, {'finished_datetime': now.strftime("%Y-%m-%d %H:%M:%S"), 'message_id': message_id})

        db_connection.commit()
        db_connection.close()
        logging.getLogger().debug('Finished..')

    async def clean_database(self):
        logging.getLogger().debug('Started..')
        db_connection = sqlite3.connect(self.connection_db_filename, timeout=30)
        cur = db_connection.cursor()
        now = datetime.now()

        sql = """DELETE FROM messages 
                            WHERE 
                            (finished_datetime IS NOT NULL AND 
                                ROUND((:now - finished_datetime) * 86400) > :diff_seconds
                            ) OR 
                            ROUND((:now - started_datetime) * 86400) > :diff_seconds + 10*60"""

        cur.execute(sql, {'now': now.strftime("%Y-%m-%d %H:%M:%S"),
                          'diff_seconds': self.connection_settings['connection_quota_seconds']})

        db_connection.commit()

        db_connection.close()
        logging.getLogger().debug('Finished..')

    async def send_message(self, message: MessageModel):
        if len(message.message_body) > self.connection_settings['connection_max_text_length']:
            raise HTTPException(status_code=413, detail="Message Body too long")

        for mandatory_key in self.connection_mandatory_keys_for_message_details:
            if mandatory_key not in message.message_details:
                raise HTTPException(status_code=422,
                                    detail=f"Mandatory Key '{mandatory_key}' not found in message_details")

        quota_check, message_id = await self.check_quota_and_insert()
        if not quota_check:
            logging.getLogger().exception(f"Sending of message failed due to quota limit reached..")
            raise HTTPException(status_code=503, detail="Quota limit for connection reached")

        try:
            return_message = await self.connection_callables['connection_send_message'](
                self,
                message
            )
            await self.update_message_in_db(message_id)
            return return_message
        except self.gateway_errors as error:
            logging.getLogger().exception(f"Sending of message failed due to Timeout Connection error..", error)
            await self.update_message_in_db(message_id)
            raise HTTPException(status_code=504, detail="Gateway TimeoutError")

    async def send_message_with_photo(self, message: MessageModel, photo_uuid: str):
        if len(message.message_body) > self.connection_settings['connection_max_text_length']:
            logging.getLogger().exception(f"Sending of message failed due to too long message body..")
            raise HTTPException(status_code=413, detail="Message Body too long")

        for mandatory_key in self.connection_mandatory_keys_for_message_details:
            if mandatory_key not in message.message_details:
                raise HTTPException(status_code=422,
                                    detail=f"Mandatory Key '{mandatory_key}' not found in message_details")

        photo_name = await self.load_file_path(photo_uuid)
        if photo_name == "":
            logging.getLogger().exception(f"Sending of message failed due to not found photo..")
            raise HTTPException(status_code=404, detail="Photo not found")

        quota_check, message_id = await self.check_quota_and_insert()
        if not quota_check:
            logging.getLogger().exception(f"Sending of message failed due to quota limit reached..")
            raise HTTPException(status_code=503, detail="Quota limit for connection reached")

        try:
            return_message = await self.connection_callables['connection_send_message_with_photo'](
                self,
                message,
                photo_name
            )
            await self.update_message_in_db(message_id)
            return return_message
        except self.gateway_errors as error:
            logging.getLogger().exception(f"Sending of message failed due to Timeout Connection error..", error)
            await self.update_message_in_db(message_id)
            raise HTTPException(status_code=504, detail="Gateway TimeoutError")

