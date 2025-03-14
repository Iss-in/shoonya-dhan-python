from conf.config import config, dhan_api, logger
from utils import dhanHelper
import os, sys, subprocess
from datetime import datetime, time
import threading
from conf.websocketService import update_timer
from services.pihole import pihole
class RiskManagement:
    def __init__(self):
        self.pnl = 0
        self.peakPnl = 0
        self.tradeCount = 0
        self.maxTradeCount = config['intraday']['maxTradeCount']
        self.qty = self.get_buy_qty('NIFTY')
        self.maxLoss = self.qty * 12 #TODO: fetch it from db
        self.lastTradeTime = datetime.today().replace(hour=9, minute=0)
        # self.lastTradeTime = datetime.now()

        self.scheduler = threading.Timer(60, self.periodic_check)
        self.scheduler.start()

        self.scheduler2 = threading.Timer(1, self.wait_timer)
        self.scheduler2.start()

    def update(self):
        self.tradeCount = dhanHelper.getTradeCount()
        self.pnl = dhanHelper.getPnl() - (40 + self.qty * 25 / 75) * self.tradeCount # TODO: change the brokerage function, appromixated currently

        if(self.pnl > self.peakPnl):
            self.peakPnl = self.pnl

    def maxLossCrossed(self):
        self.update()
        if self.pnl - self.peakPnl <= -1 * self.maxLoss:
            logger.info("cumulative max loss crossed")
            return True
        if self.tradeCount >= self.maxTradeCount:
            logger.info("max trades crossed")
            return True
        if self.pnl <= self.maxLoss * -2/3:
            logger.info("2 sl crossed")
            return True
        return False

    def get_buy_qty(self, index_name):
        indexes = config.get('intraday', {}).get('indexes', [])
        for index in indexes:
            if index.get('name') == index_name:
                return index.get('buyQty')
        return 0

    def endSession(self):
        logger.info("turning killswitch on")
        dhan_api.cancel_all_orders()
        dhan_api.kill_switch('ON')
        dhan_api.kill_switch('OFF')
        return dhan_api.kill_switch('ON')

    def killswitch(self):
        if datetime.now().time() > time(15, 30):
            return

        if self.maxLossCrossed():
            return self.endSession()
        return None


    def lockScreen(self):
        cmd = ["hyprlock", "-c", "/home/kushy/.config/hypr/hyprlock-trade.conf"]
        if os.path.exists('/.dockerenv'):
            result = subprocess.run(["docker", "run", "--rm", "alpine", "sh", "-c", cmd], capture_output=True, text=True)
        else:
            subprocess.run(cmd, capture_output=True, text=True)

    def overTrading(self):
        diff = (datetime.now() - self.lastTradeTime).total_seconds() / 60
        if diff < 15:
            return diff
        return 0

    def sanityCheck(self):

        self.lastTradeTime = datetime.now()
        logger.info("running sanity check")
        thread1 = threading.Thread(target=self.killswitch)
        thread2 = threading.Thread(target=self.lockScreen)

        # Start both threads
        thread1.start()
        thread2.start()

        # Wait for both threads to complete
        thread1.join()
        thread2.join()

        pihole.enablePihole()

    def periodic_check(self):
        self.killswitch()
        self.scheduler = threading.Timer(60, self.periodic_check)
        self.scheduler.start()

    def wait_timer(self):
        diff = (datetime.now() - self.lastTradeTime).total_seconds()
        if diff < 15* 60:
            seconds_left = int(15*60 - diff)
            minutes_left = str(int(seconds_left / 60)).zfill(2)
            seconds_left = str(seconds_left % 60).zfill(2)
            time_left = f"{minutes_left}:{seconds_left}"
            update_timer(time_left)
            self.scheduler2 = threading.Timer(1, self.wait_timer)
            self.scheduler2.start()

riskManagementobj = RiskManagement()



