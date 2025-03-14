from Dhan_Tradehull import Tradehull
import threading
from datetime import datetime
from conf.config import dhan_api, shoonya_api, logger, nifty_fut_token
from conf.websocketService import update_order_feed, send_toast
from models.partialTrade import PartialTrade
from models.DecisionPoints import decisionPoints
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

from services.riskManagement import riskManagementobj
from utils.dhanHelper import getProductType
# from conf import websocketService
import concurrent.futures
from models.DecisionPoints import decisionPoints

class TradeManager:
    def __init__(self):
        self.trades = {}
        self.ltps = dict()

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
ltps = ()

def setLtps(ltps):
    tradeManager.ltps = ltps
# subscribedTokens = []
#
#
# def subscribe(token):
#     if not token in subscribedTokens:
#         subscribedTokens.append(token);
#         shoonya_api.subscribe("NFO|" + str(token))


def placeSl(pt, token, trade):
    if trade.status > 0:
        return

    # res = shoonya_api.place_order(
    #     "S", trade.prd, trade.exch, trade.tsym,
    #     trade.qty, "STOP_LOSS", trade.slPrice, trade.slPrice + trade.diff
    # )

    logger.info(f"placing sl order for {trade.name} and token {token}")

    res = dhan_api.Dhan.place_order(security_id=token, exchange_segment="NSE_FNO", transaction_type="SELL",
                quantity=trade.qty, order_type="STOP_LOSS", product_type=trade.prd, price=trade.slPrice, trigger_price=trade.slPrice + trade.diff)
    logger.info(res)
    # Todo: fix order status when rejected
    if "data"  in res:
        orderNumber = res['data']['orderId']
        trade.orderNumber = orderNumber
        trade.status = 1
        tradeManager.updateTrade(token, pt, trade)

    logger.info(f"placed sl for a fresh order for {trade} with order number {orderNumber}")
    logger.info(f"placed sl for a fresh order for {trade.name} with order number {orderNumber}")

def manageTrade(ltp, token, pt, trade):
    if not tradeManager.hasToken(token):
        return

    points = ltp - trade.entryPrice
    targetPoints = trade.targetPrice - trade.entryPrice

    if trade.targetPrice > 0:
        if points >= 2.0 / 3 * targetPoints and trade.orderType == "STOP_LOSS":
            logger.info("modifying sl order from STOP_LOSS to LIMIT")
            logger.info(f"modifying trade {trade.to_json()}")
            # ret = dhan_api.Dhan.modify_order(order_id=trade.orderNumber, order_type="LIMIT", leg_name="ENTRY_LEG",
            #                                  quantity=trade.qty, price=trade.targetPrice, trigger_price=0, disclosed_quantity=0, validity='DAY')

            dhan_api.cancel_order(OrderID=trade.orderNumber)
            res = dhan_api.Dhan.place_order(security_id=token, exchange_segment="NSE_FNO", transaction_type="SELL",
                                            quantity=trade.qty, order_type="LIMIT", product_type=trade.prd,
                                            price=trade.targetPrice, trigger_price=0)
            trade.orderType = "LMT"
            trade.orderNumber = res['data']['orderId']
            logger.info(f"{trade.name} sl order modified from STOP_LOSS to LMT with target {trade.targetPrice}")
            logger.info(res)
        if points <= 1.0 / 3 * targetPoints and trade.orderType == "LMT":
            logger.info("modifying target order from LIMIT to STOP_LOSS")
            # ret = dhan_api.Dhan.modify_order(order_id=trade.orderNumber, order_type="STOP_LOSS", leg_name="ENTRY_LEG",
            #                                  quantity=trade.qty, price=trade.slPrice, trigger_price=trade.slPrice + trade.diff, disclosed_quantity=0, validity='DAY')
            dhan_api.cancel_order(OrderID=trade.orderNumber)
            res = dhan_api.Dhan.place_order(security_id=token, exchange_segment="NSE_FNO", transaction_type="SELL",
                                            quantity=trade.qty, order_type="STOP_LOSS", product_type=trade.prd,
                                            price=trade.slPrice, trigger_price=trade.slPrice + trade.diff)

            trade.orderType = "STOP_LOSS"
            trade.orderNumber = res['data']['orderId']
            logger.info(f"{trade.name} limit order modified from LIMIT to STOP_LOSS with sl {trade.slPrice}")
            logger.info(res)
        if ltp < trade.maxSlPrice:
            logger.info("limit sl order crossed, exiting all trades with market orders")
            # dhan_api.cancel_all_orders()
            exit_all_trades(token)
    else:

        # Trail the price using ATR method
        pass

    tradeManager.updateTrade(token, pt, trade)

def exit_all_trades(token):
    trades = tradeManager.getTrade(token)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for pt, partial_trade in trades.items():
            future_cancel = executor.submit(
                dhan_api.cancel_order,
                OrderID=partial_trade.orderNumber,
            )
            future_market_exit = executor.submit(
                dhan_api.Dhan.place_order,
                security_id=token,
                exchange_segment="NSE_FNO",
                transaction_type="SELL",
                quantity=partial_trade.qty,
                order_type="MARKET",
                product_type=partial_trade.prd,
                price=0
            )
            futures.append(future_cancel)
            futures.append(future_market_exit)

        # Ensure all futures are completed
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"Exception occurred while executing a future: {e}")

    tradeManager.removeTrade(token)


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
        futures = {executor.submit(manageTrade, ltp, token, pt, partialTrade): pt for pt, partialTrade in
                   trades.items()}
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
    product = order_update['product']
    prd = getProductType(product)

    slPrice = entryPrice - 6  # TODO: fetch from config
    maxSlPrice = entryPrice - 9
    minLotSize = 75
    targets = [20, 20]

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
                name=tradeName, status=0, qty=tradeQty, entryPrice=entryPrice, slPrice= slPrice,  maxSlPrice=maxSlPrice,
                targetPrice=entryPrice + targets[i - 1], orderType="STOP_LOSS", prd=prd, exch="NSE_NFO", tsym=tsym, diff= 0.2, token=token
            )

            tradeManager.addTrade(token, tradeName, trade)
    elif remaining > 0:
        logger.info(f"qty {qty} <= {div} x min quantity {minLotSize}")
        multiple = qty // minLotSize
        for j in range(1, multiple + 1):
            tradeName = f"t{j}"
            logger.info(f"for {tradeName}, using qty {minLotSize}")

            trade = PartialTrade(
                name=tradeName, status=0, qty=minLotSize, entryPrice=entryPrice, slPrice= slPrice,  maxSlPrice=maxSlPrice,
                targetPrice=entryPrice + targets[j - 1], orderType="STOP_LOSS", prd=prd, exch="NSE_NFO", tsym=tsym, diff= 0.2, token=token
            )
            tradeManager.addTrade(token, tradeName, trade)

    # Subscribe to token (assuming a subscribe function exists)
    # subscribe(token)


def handle_buy_order(token, order_update):
    if not tradeManager.hasToken(token):
        logger.info(f"starting a fresh trade at {datetime.now()}");
        createTrade(token, order_update)
        decisionPoints.updateDecisionPoints(tradeManager.ltps[nifty_fut_token], order_update['OptType'])

    #
    # trades = tradeManager.getTrade(token)
    #
    # with ThreadPoolExecutor(max_workers=len(trades)) as executor:
    #     futures = {executor.submit(placeSl, pt, token, partialTrade): pt for pt, partialTrade in trades.items()}
    #     for future in as_completed(futures):
    #         pt = futures[future]
    #         try:
    #             future.result()
    #         except Exception as e:
    #             logger.error(f"Error in placing SL for {pt}: {e}")


def updateSl(token, new_sl_price, order_update):
    trades = tradeManager.getTrade(token)
    old_sl_price = trades["t1"].slPrice
    executor = None
    logger.info(f"old sl price is {old_sl_price} new sl price is {new_sl_price}")
    if old_sl_price != new_sl_price:
        logger.info(f"modifying all remaining sl from {old_sl_price} to {new_sl_price}")
        try:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(trades))
            futures = []
            for pt, partial_trade in trades.items():
                partial_trade.slPrice = new_sl_price
                try:
                    if partial_trade.status == 1:
                        if partial_trade.orderNumber == order_update["orderNo"]:
                            logger.info("Sl changed manually for trade %s", partial_trade.name)
                        else:
                            logger.info("modifying sl for %s", partial_trade.name)
                            future = executor.submit(
                                dhan_api.Dhan.modify_order,
                                order_id=partial_trade.orderNumber,
                                order_type="STOP_LOSS",
                                leg_name="ENTRY_LEG",
                                quantity=partial_trade.qty,
                                price=partial_trade.slPrice,
                                trigger_price=partial_trade.slPrice + 0.2,
                                disclosed_quantity=0,
                                validity='DAY'
                            )
                            futures.append(future)
                except Exception as e:
                    logger.error(f"Exception occurred during modifying order for trade {partial_trade.name}: {e}")

        finally:
            if executor:
                executor.shutdown(wait=True)
                for future in futures:
                    try:
                        future.result()  # Ensure any raised exceptions are caught
                    except Exception as e:
                        logger.error(f"Exception occurred during modifying order: {e}")
    else:
        logger.info(f"new sl order has same price {old_sl_price}")

def handle_sell_order(token, order_update):
    if order_update['txnType'] == 'S' and order_update['status'] == 'Modified' and order_update['orderType'] == 'SL':
        logger.info(f"new manual sl order received for token {token}")
        newSlPrice = order_update['price']
        logger.info(f"new sl price is {newSlPrice}")
        updateSl(token, newSlPrice, order_update)

    elif order_update['txnType'].upper() == 'S' and order_update['status'].upper() == 'TRADED' and order_update['orderType'].upper() == 'LMT':
        logger.info(f"stop loss order triggered {order_update}")

        trades = tradeManager.getTrade(token)

        for pt, partialTrade in trades.items():
            if partialTrade.orderNumber == order_update['orderNo']:
                partialTrade.exitPrice = order_update['tradedPrice']
                partialTrade.status = 2
                tradeManager.updateTrade(token, pt, partialTrade)
                logger.info(f"{pt} completed {partialTrade.to_json()}")

        flag = True
        for partialTrade in trades.values():
            if partialTrade.status != 2:
                flag = False
                break

        if flag: # trades are completed
            logger.info(f"all active trades for token {token} completed")
            status = tradeManager.removeTrade(token)
            logger.debug(f"token {token} removed from all trades with status {status}")
            logger.info(f"All trades completed, final Trade is \n {tradeManager.trades}")

            # update last trade time
            riskManagementobj.sanityCheck()


def updateOpenOrders():
    orders =  dhan_api.Dhan.get_order_list()['data']
    openOrders = []
    for order in orders:
        if order['orderStatus'].upper() == 'PENDING':
            openOrders.append(order)
    update_order_feed(openOrders)


def handle_order(order_update: dict):
    token = order_update['securityId']
    if order_update['status'] == 'Traded' and order_update['txnType'] == 'B':
        handle_buy_order(token, order_update)
    if order_update['txnType']  == 'S':
        handle_sell_order(token, order_update)

def on_order_update(order_data: dict):
    """Optional callback function to process order data"""
    print("new order received")
    order_update = order_data.get("Data", {})
    logger.info(order_update)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(handle_order, order_update)
        executor.submit(updateOpenOrders)




def updateTargets(targets: Dict[str, float]):

    logger.info("targets are {}, {}, {}".format(targets.get("t1"), targets.get("t2"),
                                                targets.get("t3")))

    if not tradeManager.isTradeActive():
        logger.info("trade is not active")
        send_toast("Targets Update request", "Trade is not active")
        return {"message": "Trade is not active"}



    trades = tradeManager.trades

    for partial_trades in trades.values():
        for trade in partial_trades.values():
            entry_price = trade.entry_price
            initial_target_price = trade.target_price

            # update target based on name
            if trade.name == "t1":
                trade.set_target_price(targets.get("t1") + entry_price)
            if trade.name == "t2":
                trade.set_target_price(targets.get("t2") + entry_price)
            if trade.name == "t3":
                trade.set_target_price(targets.get("t3") + entry_price)

            # change limit order price if already in place
            if trade.order_type == "LMT":
                ret = dhan_api.Dhan.modify_order(order_id=trade.orderNumber, order_type="LIMIT", quantity=trade.qty,
                                                 price=trade.targetPrice)

                logger.info(
                    "LMT order of trade {} got modified from {} to {}".format(trade.name, initial_target_price,
                                                                              trade.target_price))
                logger.info(ret)
    # websocketService.send_toast("Targets Update request", "Targets Updated")
    return 0
