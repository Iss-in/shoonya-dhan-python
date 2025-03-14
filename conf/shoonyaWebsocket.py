from datetime import datetime
from conf.config import logger,  shoonya_api, nifty_fut_token
from services.tradeManagement import manageOptionSl, setLtps
import threading
from services.optionUpdate import optionUpdateObj
import time
import concurrent.futures
from conf.websocketService import send_price_feed
# from services.charts import chart
import pandas as pd
# update nifty spot price in consul via feed
feed_opened = False
socket_opened = False
feedJson={}
ltps=dict()
current_chart_token = 0

def setChartToken(token):
    global current_chart_token
    current_chart_token = token

def event_handler_feed_update(tick_data):
    global current_chart_token
    UPDATE = False
    if 'tk' in tick_data:
        token = tick_data['tk']
        timest = datetime.fromtimestamp(int(tick_data['ft'])).isoformat()
        feed_data = {'tt': timest}
        epoch = tick_data.get("ft")

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
                        ltps[token] = float(feed_data['ltp'])
                        # manageOptionSl(token, float(feedJson[token]['ltp']))
                        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                            futures = []
                            futures.append(executor.submit(manageOptionSl, token, float(feedJson[token]['ltp'])))
                            futures.append(executor.submit(send_price_feed, token, epoch, float(feedJson[token]['ltp'])))
                            futures.append(executor.submit(setLtps, ltps))
                            for future in futures:
                                try:
                                    future.result()
                                except Exception as e:
                                    logger.error(f"Exception occurred while executing a future: {e}")

                    except Exception as err:
                        logger.error(f"error with feed occured {err}")
                    if token == str(current_chart_token):
                        tick = {'time': timest, 'price': float(feed_data['ltp']), 'volume': 0}
                        # chart.update_from_tick(pd.Series(tick))
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
    print("Shoonya websocketService.py opened")

def setupWebSocket():
    global feed_opened
    logger.info("waiting for shoonya websocketService.py opening")
    shoonya_api.start_websocket(order_update_callback=event_handler_order_update,
                         subscribe_callback=event_handler_feed_update,
                         socket_open_callback=open_callback)
    while(feed_opened==False):
        pass


def optionUpdate():
    while(True):
        if '26000' in ltps:
            optionUpdateObj.updateOptions(int(ltps['26000']))
        time.sleep(60)

def start_shoonya_websocket():
    # Create and start a daemon thread so that it won't block shutdown.
    thread = threading.Thread(target=setupWebSocket, daemon=True)
    thread.start()
    logger.info("feed websocketService.py started")
    shoonya_api.subscribe("NSE|26000")
    shoonya_api.subscribe("NFO|"+nifty_fut_token)


    print("starting options update")
    thread = threading.Thread(target=optionUpdate, daemon=True)
    thread.start()


