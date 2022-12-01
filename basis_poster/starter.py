import threading

import uvicorn

from basis_poster.Connection import Connection
from basis_poster.cleaning import start_cleaning
from basis_poster.fastapi import app


def start():
    Connection.check_directories()
    cleaning_thread = threading.Thread(target=start_cleaning, name='Cleaning')
    fastapi_thread = threading.Thread(target=start_api, name='Cleaning')

    cleaning_thread.start()
    fastapi_thread.start()

    cleaning_thread.join()
    fastapi_thread.join()


def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)
