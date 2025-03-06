from Dhan_Tradehull import Tradehull
import threading
from datetime import datetime
from conf.config import dhan_api, shoonya_api, logger
from models.partialTrade import  PartialTrade
from concurrent.futures import ThreadPoolExecutor, as_completed

class TradeManager:
    def __init__(self):
        self.trades = {}

    def addTrade(self, token, tradeName, trade):
        if token not in self.trades:
            self.trades[token] = {}
        self.trades[token][tradeName] = trade

    def getTrade(self, token):
        return self.trades.get(token, {})

    def removeTrade(self, token):
        if token in self.trades:
            del self.trades[token]
            return True
        return False

    def updateTrade(self, token, pt, partialTrade):
        if token in self.trades:
            self.trades[token][pt] = partialTrade

    def hasToken(self, token):
        return token in self.trades

    def isTradeActive(self):
        return len(self.trades) != 0


tradeManager = TradeManager()
subscribedTokens = []
def subscribe( token):
        if not subscribedTokens.contains(token):
            subscribedTokens.add(token);
            shoonya_api.subscribe("NFO|" + str(token))


def placeSl(pt, token, trade):
    if trade.status > 0:
        return
    logger.info(f"placing sl for a fresh order for {trade}")
    logger.info(f"placing sl for a fresh order for {trade.name}")
    res = shoonya_api.place_order(
        "S", trade.prd, trade.exch, trade.tsym,
        trade.qty, "SL-LMT", trade.slPrice, trade.slPrice + trade.diff
    )

    orderNumber = res.get("norenordno")
    if "resreason" not in res:
        trade.orderNumber = orderNumber
        trade.status = 1
        tradeManager.updateTrade(token, pt, trade)

def manageTrade(ltp, token, pt, trade):
    if not tradeManager.hasToken(token):
        return

    points = ltp - trade.entryPrice
    targetPoints = trade.targetPrice - trade.entryPrice
    ret = None

    if trade.targetPrice > 0:
        if points >= 2.0 / 3 * targetPoints and trade.orderType == "SL-LMT":
            logger.info("modifying sl order from SL-LMT to LIMIT")
            ret = shoonya_api.modify_order(
                trade.exch, trade.tsym, trade.orderNumber, trade.qty,
                "LMT", trade.targetPrice, None
            )
            trade.orderType = "LMT"
            logger.info(f"sl order modified from SL-LMT to LMT with target {trade.targetPrice}")
            logger.info(ret)
        if points <= 1.0 / 3 * targetPoints and trade.orderType == "LMT":
            logger.info("modifying target order from LIMIT to SL-LMT")
            ret = shoonya_api.modify_order(
                trade.exch, trade.tsym, trade.orderNumber, trade.qty,
                "SL-LMT", trade.slPrice, trade.slPrice + trade.diff
            )
            trade.orderType = "SL-LMT"
            logger.info(f"sl order modified from LIMIT to SL-LMT with sl {trade.slPrice}")
            logger.info(ret)
        if ltp < trade.maxSlPrice:
            logger.info("limit sl order crossed, exiting all trades with market orders")
            exitAllCurrentTrades(token)
    else:
        # Trail the price using ATR method
        pass

    tradeManager.updateTrade(token, pt, trade)

    
def manageOptionSl(token, ltp):
    if not tradeManager.hasToken(token):
        logger.debug("trade status false or current token is not of current trade")
        return

    trades = tradeManager.getTrade(token)

    with ThreadPoolExecutor(max_workers=len(trades)) as executor:
        futures = {executor.submit(placeSl, pt, token, partialTrade): pt for pt, partialTrade in trades.items()}
        for future in as_completed(futures):
            pt = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in placing SL for {pt}: {e}")

    trades = tradeManager.getTrade(token)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(manageTrade, ltp, token, pt, partialTrade): pt for pt, partialTrade in trades.items()}
        for future in as_completed(futures):
            pt = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in managing trade for {pt}: {e}")

    
def createTrade(token, order_update):
    qty = order_update['quantity']
    entryPrice = order_update['tradedPrice']
    tsym = order_update['displayName']
    
    slPrice = 5  # TODO: fetch from config
    maxSlPrice = 8
    minLotSize = 75
    targets = [20, 20, 20]

    div = len(targets)
    multiple = qty // (div * minLotSize)
    remaining = qty % (div * minLotSize)

    logger.info(f"order qty {qty} = {minLotSize} X {multiple} + {remaining}")

    if multiple > 0:
        logger.info(f"qty {qty} is greater than or equal to 3x min_quantity {minLotSize}")

        for i in range(div, 0, -1):
            tradeName = f"t{i}"
            tradeQty = minLotSize * multiple
            if remaining > 0:
                tradeQty += minLotSize
                remaining -= minLotSize

            logger.info(f"for {tradeName}, using qty {tradeQty}")
            trade = PartialTrade(
                tradeName, 0, tradeQty, entryPrice, slPrice, maxSlPrice,
                entryPrice + targets[i - 1], "SL-LMT", "pcode", "exch", tsym, "diff", token
            )

            tradeManager.addTrade(token, tradeName, trade)
    elif remaining > 0:
        logger.info(f"qty {qty} <= {div} x min quantity {minLotSize}")
        multiple = qty // minLotSize
        for j in range(1, multiple + 1):
            tradeName = f"t{j}"
            logger.info(f"for {tradeName}, using qty {minLotSize}")

            trade = PartialTrade(
                tradeName, 0, minLotSize, entryPrice, slPrice, maxSlPrice,
                entryPrice + targets[j - 1], "SL-LMT", "pcode", "exch", tsym, "diff", token
            )
            tradeManager.addTrade(token, tradeName, trade)

    # Subscribe to token (assuming a subscribe function exists)
    subscribe( token)

def handle_buy_order(token, order_update):
    if not tradeManager.hasToken(token):
        logger.info(f"starting a fresh trade at {datetime.now()}");
        createTrade(token, order_update)

def handle_sell_order(token, order_update):
    if order_update['txnType'] == 'S' and order_update['status'] == 'Pending' and order_update['orderType'] == 'SL':
        logger.debug("new manual sl order received")
        # TODO: update updateSl function
        # newSlPrice = order_update['price']
        # updateSl(token, newSlPrice, order_update)

    if order_update['txnType'] == 'S' and order_update['status'] == 'Triggered' and order_update['orderType'] == 'LMT':
        logger.info(f"stop loss order triggered {order_update}")

        trades = tradeManager.getTrade(token)

        for pt, partialTrade in trades.items():
            if partialTrade.orderNumber == order_update['exchOrderNo']:
                partialTrade.exitPrice = order_update['tradedPrice']
                partialTrade.status = 2
                tradeManager.updateTrade(token, pt, partialTrade)
                logger.info(f"{pt} completed {partialTrade}")

        flag = True
        for partialTrade in trades.values():
            if partialTrade.status != 2:
                flag = False
                break

        if flag:
            logger.info(f"all active trades for token {token} completed")
            status = tradeManager.removeTrade(token)
            logger.debug(f"token {token} removed from all trades with status {status}")
            logger.info(f"All trades completed, final Trade is \n {tradeManager.trades}")
            # TODO: run a command to lock screen

def on_order_update(order_data: dict):
    """Optional callback function to process order data"""
    print("new order received")
    order_update = order_data.get("Data", {})
    logger.info(order_update)
    
    token = order_update['securityId']
    if order_update['status'] == 'Traded' and order_update['txnType' == 'B']:
        handle_buy_order(token, order_update)
    if order_update['status'] == 'Traded' and order_update['txnType' == 'S']:
        handle_sell_order(token, order_update)