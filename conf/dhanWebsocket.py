from services import tradeManagement 
from dhanhq import  orderupdate
from conf.config import client_id, access_token, logger
import threading
import time


''' 
subscribe to dhan order websocket.py 
'''

def run_order_update():
    order_client = orderupdate.OrderSocket(client_id, access_token)
    order_client.on_update = tradeManagement.on_order_update
    # order_client.connect_to_dhan_websocket_sync()
    while True:
        try:
            order_client.connect_to_dhan_websocket_sync()
        except Exception as e:
            print(f"Error connecting to Dhan WebSocket: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

def start_dhan_websocket():
    # Create and start a daemon thread so that it won't block shutdown.
    thread = threading.Thread(target=run_order_update, daemon=True)
    thread.start()
    logger.info(f"dhan websocket.py started")