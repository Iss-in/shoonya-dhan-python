from websocket_server import WebsocketServer
import threading
import json
from queue import Queue
from utils.loggerHelper import logger

queue = Queue()

def send_message(message):
    try:
        queue.put(message)
        process_queue()
    except Exception as e:
        logger.error(f"Failed to queue message: {e}")

def process_queue():
    while not queue.empty():
        try:
            next_message = queue.get()
            if next_message:
                send_message(next_message)
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
        "ceToken": ce_token,
        "peToken": pe_token,
        "ceTsym": ce_tsym,
        "peTsym": pe_tsym
    }
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
