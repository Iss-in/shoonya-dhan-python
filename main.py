from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from conf.dhanWebsocket import start_dhan_websocket
from conf.shoonyaWebsocket import start_shoonya_websocket
from conf.config import logger

from api.endpoints import riskController , testController
from pydantic import BaseModel
import uvicorn

# Initialize the FastAPI app
app = FastAPI()
# Include the routers
app.include_router(riskController.router)
app.include_router(testController.router)

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

# Define a WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")


# Run the FastAPI app with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)