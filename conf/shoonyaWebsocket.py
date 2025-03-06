from datetime import datetime
from conf.config import logger,  shoonya_api
from services.tradeManagement import manageOptionSl
import threading
# update nifty spot price in consul via feed
feed_opened = False
socket_opened = False
feedJson={}

def event_handler_feed_update(tick_data):
    UPDATE = False
    if 'tk' in tick_data:
        token = tick_data['tk']
        timest = datetime.fromtimestamp(int(tick_data['ft'])).isoformat()
        feed_data = {'tt': timest}
        if 'lp' in tick_data:
            feed_data['ltp'] = float(tick_data['lp'])
        if 'ts' in tick_data:
            feed_data['Tsym'] = str(tick_data['ts'])
        if 'oi' in tick_data:
            feed_data['openi'] = float(tick_data['oi'])
        if 'poi' in tick_data:
            feed_data['pdopeni'] = str(tick_data['poi'])
        if 'v' in tick_data:
            feed_data['Volume'] = str(tick_data['v'])
        if feed_data:
            # print(feed_data)
            UPDATE = True
            if token not in feedJson:
                feedJson[token] = {}
            feedJson[token].update(feed_data)

        if UPDATE:
                if 'ltp' in feed_data:
                    try:
                        manageOptionSl(token, float(feedJson[token]['ltp']))
                        # print(token, float(feedJson[token]['ltp']) )
                    except Exception as err:
                        logger.error(f"error with feed occured {err}")

def update_orders(order_update):
    pass
def event_handler_order_update(order_update):
    logger.debug(f"order feed {order_update}")
    try:
        update_orders(order_update)
    except Exception as err:
        logger.error(f"update order error occoured {err}")

def open_callback():
    global feed_opened
    feed_opened = True
    print("Shoonya websocket.py opened")

def setupWebSocket():
    global feed_opened
    logger.info("waiting for shoonya websocket.py opening")
    shoonya_api.start_websocket(order_update_callback=event_handler_order_update,
                         subscribe_callback=event_handler_feed_update,
                         socket_open_callback=open_callback)
    while(feed_opened==False):
        pass


def start_shoonya_websocket():
    # Create and start a daemon thread so that it won't block shutdown.
    thread = threading.Thread(target=setupWebSocket, daemon=True)
    thread.start()
    logger.info("feed websocket.py started")
    shoonya_api.subscribe("NFO|26000")
