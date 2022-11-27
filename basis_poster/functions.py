from __future__ import annotations

import logging
import os
import sqlite3
import time

import yaml


def split_text_by_length(raw_text: str, delimiter: list[str], max_text_length: int = 500):
    if not delimiter:
        return [raw_text[i:i + max_text_length] for i in range(0, len(raw_text), max_text_length)]

    refined_texts = []
    current_delimiter = delimiter.pop(0)
    for part_text in raw_text.split(current_delimiter):
        if len(part_text) < max_text_length + 1:
            refined_texts.append(part_text + current_delimiter)
            continue
        refined_texts += split_text_by_length(part_text + current_delimiter, delimiter, max_text_length)

    return refined_texts


def split_text_for_platform(raw_text: str, max_text_length: int = 500) -> list[str]:
    logging.getLogger().debug('Started..')
    if len(raw_text) <= max_text_length:
        return [raw_text]

    split_texts = split_text_by_length(raw_text, ['.', ',', ' '], max_text_length)

    post_counter = 0
    posts = [""]
    for text in split_texts:
        if len(posts[post_counter]) + len(text) <= max_text_length:
            posts[post_counter] += text
        else:
            post_counter += 1
            posts.append(text)
    logging.getLogger().debug('Finished..')
    return posts


def load_pictures_names(pictures_dir: str, pictures_ids: str):
    logging.getLogger().debug('Started..')
    if not pictures_ids:
        return []
    pictures_names = []

    for picture_id in pictures_ids.split("|"):
        file_names = find_file(picture_id, pictures_dir)
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


async def check_for_db_and_connections_files(files: list[str], dirs: list[str]):
    while True:
        all_exist = True
        for file_name in files:
            if not os.path.isfile(file_name):
                all_exist = False
                break
        for dir_name in dirs:
            if not os.path.isdir(dir_name):
                all_exist = False
                break
        if all_exist:
            return

        logging.getLogger().info(f"Not all necessary files or directories in data are yet existent. Retrying in 10 "
                                 f"seconds.")
        time.sleep(10)


def load_connections_from_file(connections_filename: str):
    logging.getLogger().debug('Started..')
    with open(connections_filename, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    logging.getLogger().debug('Finished..')
