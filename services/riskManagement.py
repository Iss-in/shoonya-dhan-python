from conf.config import config, dhan_api, logger
from utils import dhanHelper
import os, sys, subprocess

class RiskManagement:
    def __init__(self):
        self.pnl = 0
        self.peakPnl = 0
        self.tradeCount = 0
        self.maxTradeCount = config['intraday']['maxTradeCount']
        self.qty = self.get_buy_qty('NIFTY')
        self.maxLoss = 2000 #TODO: fetch it from db

    def update(self):
        self.tradeCount = dhanHelper.getTradeCount()
        self.pnl = dhanHelper.getPnl() - (40 + self.qty * 25 / 75) * self.tradeCount # TODO: change the brokerage function, appromixated currently

        if(self.pnl > self.peakPnl):
            self.peakPnl = self.pnl

    def maxLossCrossed(self):
        self.update()
        if self.pnl - self.peakPnl <= -1 * self.maxLoss:
            return True
        if self.tradeCount >= self.maxTradeCount:
            return True
        if self.pnl <= self.maxLoss * -2/3:
            return True
        return False

    def get_buy_qty(self, index_name):
        indexes = config.get('intraday', {}).get('indexes', [])
        for index in indexes:
            if index.get('name') == index_name:
                return index.get('buyQty')
        return 0

    def killswitch(self):
        if self.maxLossCrossed():
            logger.info("turning killswitch on")
            return dhan_api.kill_switch('ON')
        return None


    def lockScreen(self):
        cmd = ["hyprlock", "-c", "/home/kushy/.config/hypr/hyprlock-trade.conf"]
        if os.path.exists('/.dockerenv'):
            result = subprocess.run(["docker", "run", "--rm", "alpine", "sh", "-c", cmd], capture_output=True, text=True)
        else:
            subprocess.run(cmd, capture_output=True, text=True)


riskManagementobj = RiskManagement()

# riskManagementobj.update()
# print(riskManagementobj.pnl)
# print(riskManagementobj.peakPnl)
# print(riskManagementobj.tradeCount)
# print(riskManagementobj.maxTradeCount)
# print(riskManagementobj.qty)
# print(riskManagementobj.maxLoss)
#





