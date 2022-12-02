from fastapi import FastAPI, HTTPException

from basis_poster.Connection import Connection
from basis_poster.models import (
    MessageModel, MessageReturnModel, MessagePhotoReturnModel,
    ConnectionModel, ConnectionInputModel)

app = FastAPI()


@app.get("/")
async def root():
    return {'message': 'Welcome to a Poster-Basis API'}


@app.post("/connection/{connection_uuid}/send_message", response_model=MessageReturnModel)
async def send_message(connection_uuid: str, message: MessageModel):
    if connection_uuid not in Connection.connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    return await Connection.connections[connection_uuid].send_message(message)


@app.post("/connection/{connection_uuid}/send_message_with_photo/{photo_uuid}", response_model=MessagePhotoReturnModel)
async def send_message_with_photo(connection_uuid: str, photo_uuid: str, message: MessageModel):
    if connection_uuid not in Connection.connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    return await Connection.connections[connection_uuid].send_message_with_photo(message, photo_uuid)


@app.post("/connection", response_model=ConnectionModel)
async def add_connection(connection_data: ConnectionInputModel):
    connection = Connection.create_connection(connection_data)
    return connection.get_connection_model()


@app.delete("/connection/{connection_uuid}")
async def delete_connection(connection_uuid: str):
    if connection_uuid not in Connection.connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    del(Connection.connections[connection_uuid])


@app.patch("/connection/{connection_uuid}", response_model=ConnectionModel)
async def change_connection(connection_uuid: str, connection_data: ConnectionInputModel):
    if connection_uuid not in Connection.connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    del(Connection.connections_name_to_uuids[Connection.connections[connection_uuid].connection_name])
    connection = Connection(connection_data, connection_uuid)
    return connection.get_connection_model()


@app.get("/connection/{connection_uuid}", response_model=ConnectionModel)
async def get_connection(connection_uuid: str):
    if connection_uuid not in Connection.connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    return Connection.connections[connection_uuid].get_connection_model()
