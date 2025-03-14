from conf.config import config, dhan_api, shoonya_api, logger
from services.tradeManagement import tradeManager
from utils.misc import misc
import math, mibian
from datetime import datetime
from conf import websocketService
import schedule, time
import redis
import json


r = redis.Redis(host='localhost', port=6379, db=0)

# from conf.shoonyaWebsocket import setChartToken
class optionUpdate:
    def __init__(self):
        self.delta = config['intraday']['delta']
        self.callPrice = 20000
        self.putPrice = 20000
        self.expiry_date = misc.get_nse_weekly_expiry('NIFTY', 0)
        self.subscribedTokens = ['26000']
        self.ltp = self.getLtp()
        self.getTokens(self.ltp)
        logger.info(f"using expiry {self.expiry_date}")

    def getLtp(self):
        res = shoonya_api.get_quotes(exchange="NSE", token='26000')
        ltp =  int(float(res['lp']))
        return round(ltp / 50) * 50

    def getTokens(self, ltp):
        spot_price = round(ltp / 50) * 50
        self.callSymbol = "NIFTY " + self.expiry_date.strftime("%d %b ").upper() + str(spot_price) + " CALL"
        self.putSymbol = "NIFTY " +  self.expiry_date.strftime("%d %b ").upper() + str(spot_price) + " PUT"
        self.callToken = dhan_api.get_security_id(self.callSymbol, "NFO")
        self.putToken = dhan_api.get_security_id(self.putSymbol, "NFO")

    def  getCallDelta(self, strike_price, spot_price):
        current_date = datetime.now().strftime('%d-%m-%y')
        # expiry_date = misc.get_nse_weekly_expiry('NIFTY', 0)

        # expiry = datetime.strptime(expiry_date, '%d-%m-%y').replace(hour=15, minute=30, second=0, microsecond=0)
        expiry = self.expiry_date.replace(hour=15, minute=30, second=0, microsecond=0)
        now = datetime.strptime(current_date, '%d-%m-%y')

        seconds = math.floor((expiry-now).total_seconds())
        minutes = math.floor(seconds/60)
        hours = math.floor(minutes/60)
        days = seconds/86400

        c = mibian.BS([spot_price, strike_price, 7, days], volatility=18)
        return c.callDelta

    def find_index_descending(self, lst):
        for index in range(len(lst) - 1, -1, -1):
            if lst[index] > self.delta:
                return index
        return -1

    def find_index_ascending(self, lst):
        for index, value in enumerate(lst):
            if value > self.delta:
                return index
        return -1

    def updateOptions(self, spot_price:int = 0, firstFetch=False ):

        # do not update options if trade is active
        if tradeManager.isTradeActive():
            return

        if spot_price == 0:
            spot_price = self.ltp
        else:
            spot_price = round(spot_price / 50) * 50

        strike_list = list(range(spot_price - 5*50, spot_price + 5*50 + 1, 50))
        call_delta_list = list(map(lambda x: self.getCallDelta(x, spot_price), strike_list))
        put_delta_list = list(map(lambda x: 1 - x, call_delta_list))

        callPrice = strike_list[self.find_index_descending(call_delta_list)]
        putPrice = strike_list[self.find_index_ascending(put_delta_list)]

        if firstFetch:
            self.callPrice = 0
            self.putPrice = 0
            self.subscribedTokens = ['26000']

        flag = 0
        if callPrice != self.callPrice:
            self.callPrice = callPrice
            self.callSymbol = "NIFTY " +  self.expiry_date.strftime("%d %b ").upper() + str(callPrice) + " CALL"
            shoonya_api.unsubscribe("NFO|"+ str(self.callToken))
            self.callToken = dhan_api.get_security_id(self.callSymbol, "NFO")
            if self.callToken not in self.subscribedTokens:
                shoonya_api.subscribe("NFO|"+ str(self.callToken))
                self.subscribedTokens.append(self.callToken)

            flag = 1

        if putPrice != self.putPrice:
            self.putPrice = putPrice
            self.putSymbol = "NIFTY " +  self.expiry_date.strftime("%d %b ").upper() + str(putPrice) + " PUT"
            shoonya_api.unsubscribe("NFO|"+ str(self.putToken))
            self.putToken = dhan_api.get_security_id(self.putSymbol, "NFO")
            if self.putToken not in self.subscribedTokens:
                shoonya_api.subscribe("NFO|"+ str(self.putToken))
                self.subscribedTokens.append(self.putToken)
            flag = 1

        if flag == 1 or firstFetch:
            websocketService.update_atm_options(self.callToken, self.callSymbol, self.putToken, self.putSymbol)
            r.publish('channel1', f"{self.callToken} {self.callSymbol} {self.putToken} {self.putSymbol}")
            # changeChart(self.callToken)

optionUpdateObj = optionUpdate()