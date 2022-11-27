from __future__ import annotations

import logging
import os
import sqlite3
import time

import yaml

DATABASE_FILENAME = "data/shared_messages.db"


def split_text_for_mastodon(raw_text: str = None) -> list[str]:
    logging.getLogger().debug('Started..')
    if len(raw_text) < 501:
        return [raw_text]

    splitted_text_raw = raw_text.split('.')
    post_counter = 0
    posts = [""]
    for text in splitted_text_raw:
        if len(posts[post_counter]) + len(text) < 500:
            posts[post_counter] += text + '.'
        else:
            post_counter += 1
            posts.append(text)
    logging.getLogger().debug('Finished..')
    return posts


def load_pictures_names(pictures_ids: str):
    logging.getLogger().debug('Started..')
    if not pictures_ids:
        return []
    pictures_names = []

    for picture_id in pictures_ids.split("|"):
        file_names = find_file(picture_id, 'data/pictures')
        if file_names:
            pictures_names.append(file_names[0])

    logging.getLogger().debug('Finished..')
    return pictures_names


def find_file(file_name, directory_name):
    logging.getLogger().debug('Started..')
    files_found = []
    for path, subdirs, files in os.walk(directory_name):
        for name in files:
            if name.find(file_name) > -1:
                file_path = os.path.join(path, name)
                files_found.append(file_path)
    logging.getLogger().debug('Finished..')
    return files_found


async def send_sql(db_filename: str, sql: list[str] | str, data: list[tuple] | tuple = None):
    logging.getLogger().debug('Started..')
    if isinstance(sql, list):
        for sql_row in sql:
            await send_sql(db_filename, sql_row)
        return
    db_connection = sqlite3.connect(db_filename, timeout=30)
    cur = db_connection.cursor()

    if isinstance(data, list):
        cursor_execute_function = cur.executemany
    else:
        cursor_execute_function = cur.execute

    if data:
        cursor_execute_function(sql, data)
    else:
        cursor_execute_function(sql)
    last_id = cur.lastrowid
    db_connection.commit()
    db_connection.close()
    logging.getLogger().debug('Finished..')
    return last_id


async def get_from_db(db_filename: str, sql: str, data: tuple = None):
    logging.getLogger().debug('Started..')
    db_connection = sqlite3.connect(db_filename, timeout=30)
    cur = db_connection.cursor()

    if data:
        result = cur.execute(sql, data)
    else:
        result = cur.execute(sql)

    return_list = result.fetchall()
    db_connection.close()
    logging.getLogger().debug('Finished..')
    return return_list


async def check_for_db_and_connections_files():
    while True:
        if os.path.isfile("data/connections.yaml") and os.path.isfile("data/shared_messages.db") and \
                os.path.isdir("data/pictures"):
            return
        logging.getLogger().info(f"Not all necessary files or directories in data are yet existent. Retrying in 10 "
                                 f"seconds.")
        time.sleep(10)


def load_connections_from_file():
    logging.getLogger().debug('Started..')
    with open("data/connections.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    logging.getLogger().debug('Finished..')
