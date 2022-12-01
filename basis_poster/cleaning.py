from apscheduler.schedulers.asyncio import AsyncIOScheduler

from basis_poster.Connection import Connection


async def start_cleaning():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cleaning_runner, 'interval', minutes=5)


async def cleaning_runner():
    for connection_uuid in Connection.connections:
        Connection.connections[connection_uuid].clean_database()
