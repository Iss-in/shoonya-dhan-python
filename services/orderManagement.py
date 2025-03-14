from conf.config import dhan_api, shoonya_api, logger, nifty_fut_token
from services.riskManagement import riskManagementobj
from conf import websocketService
from models.DecisionPoints import decisionPoints
from conf.shoonyaWebsocket import ltps
def buyOrder(token, order_type, price):

    # symbol = dhan_api.get_security_id(symbol)
    option_type = dhan_api.get_trading_symbol(int(token)).split(' ')[-1]
    triggerPrice = 0.0
    if order_type == "STOP_LOSS":
        triggerPrice = price - 0.2

    if order_type == "SL":
        logger.info(f"sl order with sl as {price} and buy price at {price + 4}")
        price = price + 4

    minutes_left = riskManagementobj.overTrading()
    if minutes_left:
        websocketService.send_toast("overtrading", f"wait for {minutes_left} minutes")
        return

    if not decisionPoints.checkTradeValidity(ltps[nifty_fut_token], option_type):
        websocketService.send_toast("Wrong trade", "Price not near any DP")
        return

    res = dhan_api.Dhan.place_order(security_id=token, exchange_segment="NSE_FNO", transaction_type="BUY",
                quantity=riskManagementobj.qty, order_type=order_type, product_type="INTRADAY", price=price, trigger_price=triggerPrice)

    logger.info(f"Manual buy order status")
    logger.info(res)


def modifyActiveOrder(orderId, newPrice):

    order = dhan_api.get_order_detail(orderId)

    if order["orderType"] == "LIMIT":
        # shoonyaHelper.modifyOrder(order["exch"], order["tsym"], norenordno, order["qty"], "LMT", newPrice, 0.0)
        dhan_api.Dhan.modify_order(order_id=orderId, order_type="LIMIT", leg_name="ENTRY_LEG",quantity=order["quantity"],
                                   price=newPrice, trigger_price=0, disclosed_quantity=0, validity='DAY')

    type_modifier = -1 if order["transactionType"] == "BUY" else 1
    if order["orderType"] == "STOP_LOSS":
        # shoonyaHelper.modifyOrder(order["exch"], order["tsym"], norenordno, order["qty"], "SL-LMT", newPrice, newPrice + 0.2 * type_modifier)

            # ret = dhan_api.Dhan.modify_order(order_id=trade.orderNumber, order_type="LIMIT", leg_name="ENTRY_LEG",
            #                                  quantity=trade.qty, price=trade.targetPrice, trigger_price=0, disclosed_quantity=0, validity='DAY')

        dhan_api.Dhan.modify_order(order_id=orderId, order_type="STOP_LOSS", leg_name="ENTRY_LEG",quantity=order["quantity"],
                                   price=newPrice, trigger_price=newPrice + type_modifier * 0.2, disclosed_quantity=0, validity='DAY')
