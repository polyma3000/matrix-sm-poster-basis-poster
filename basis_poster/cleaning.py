import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from basis_poster.Connection import Connection


def start_cleaning():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(cleaning_runner, 'interval', minutes=5)
    scheduler.start()


async def cleaning_runner():
    for connection_uuid in Connection.connections:
        Connection.connections[connection_uuid].clean_database()
