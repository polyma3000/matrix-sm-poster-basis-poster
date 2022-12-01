from fastapi import FastAPI, HTTPException

from basis_poster.Connection import Connection
from basis_poster.models import (
    MessageModel, MessageReturnModel, MessagePhotoReturnModel,
    ConnectionModel, ConnectionInputModel)

app = FastAPI()


@app.get("/")
async def root():
    return {'message': 'Welcome to a Poster-Basis API'}


@app.post("/{connection_uuid}/send_message", response_model=MessageReturnModel)
async def send_message(connection_uuid: str, message: MessageModel):
    if connection_uuid not in Connection.connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    return await Connection.connections[connection_uuid].send_message(message)


@app.post("/{connection_uuid}/send_message_with_photo/{photo_uuid}", response_model=MessagePhotoReturnModel)
async def send_message_with_photo(connection_uuid: str, photo_uuid: str, message: MessageModel):
    if connection_uuid not in Connection.connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    return await Connection.connections[connection_uuid].send_message_with_photo(message, photo_uuid)


@app.post("/add_connection", response_model=ConnectionModel)
async def add_connection(connection_data: ConnectionInputModel):
    connection = Connection.create_connection(connection_data)
    return connection.get_connection_model()
