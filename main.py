from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from conf.dhanWebsocket import start_dhan_websocket
from conf.shoonyaWebsocket import start_shoonya_websocket
from conf.config import logger
from services import charts

from api.endpoints import riskController , testController, orderController, pollingController

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import uvicorn

from conf.websocketService import connection_manager

# Initialize the FastAPI app
app = FastAPI()
# Include the routers
app.include_router(riskController.router)
app.include_router(testController.router)
app.include_router(orderController.router)
app.include_router(pollingController.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define the startup function
async def startup_function():
    logger.info("Application has started!")
    start_shoonya_websocket()
    start_dhan_websocket()

# Define the shutdown function
async def shutdown_function():
    print("Application is shutting down!")

# Define the lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_function()
    yield
    await shutdown_function()

# Assign the lifespan context to the app
app.router.lifespan_context = lifespan




# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []
#
#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#
#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)
#
#     async def send_message(self, message: str):
#         for connection in self.active_connections:
#             await connection.send_text(message)
#
# connection_manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        print("Client disconnected")


# Run the FastAPI app with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)