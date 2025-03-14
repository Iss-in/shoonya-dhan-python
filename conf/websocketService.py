from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import threading
import json
from queue import Queue
from conf.config import logger
# from main import connection_manager
from typing import List
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

connection_manager = ConnectionManager()

queue = Queue()

def send_message(message):
    try:
        queue.put(message)
        asyncio.run(process_queue())
    except Exception as e:
        logger.error(f"Failed to queue message: {e}")

async def process_queue():
    while not queue.empty():
        try:
            next_message = queue.get()
            if next_message:
                await connection_manager.send_message(next_message)
                logger.debug(f"Sent message: {next_message}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

def send_toast(title, description):
    res = {
        "type": "toast",
        "title": title,
        "description": description
    }
    send_message(json.dumps(res))

def send_price_feed(token, epoch, price):
    res = {
        "type": "price",
        "token": token,
        "tt": epoch,
        "price": price
    }
    send_message(json.dumps(res))

def update_atm_options(ce_token, ce_tsym, pe_token, pe_tsym):
    res = {
        "type": "atm",
        "ceToken": int(ce_token),
        "peToken": int(pe_token),
        "ceTsym": ce_tsym,
        "peTsym": pe_tsym
    }
    print(res)
    send_message(json.dumps(res))

def update_order_feed(orders):
    res = {
        "type": "order",
        "orders": orders
    }
    send_message(json.dumps(res))

def update_position_feed(positions):
    res = {
        "type": "position",
        "positions": positions
    }
    send_message(json.dumps(res))

def update_timer(timer):
    res = {
        "type": "timer",
        "left": timer
    }
    send_message(json.dumps(res))

# Called for every client connecting (after handshake)
def new_client(client, server):
    print(f"New client connected and was given id {client['id']}")

# Called for every client disconnecting
def client_left(client, server):
    print(f"Client {client['id']} disconnected")
