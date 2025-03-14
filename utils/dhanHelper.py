from conf.config import dhan_api
from utils.loggerHelper import logger

def getPnl():
    positions = dhan_api.get_positions()
    if positions.empty:
        return 0

    pnl = positions['realizedProfit'].sum() + positions['unrealizedProfit'].sum()
    return pnl

def getTradeCount():
    df = dhan_api.get_trade_book()

    if isinstance(df, dict):
        logger.error(f"error getting trade book info: {df}")
        return 0

    if df.empty:
        return 0

    trades = df[df['orderStatus'] == 'TRADED']
    trade_count = 0
    buy_qty = 0
    sell_qty = 0


    # Parse through DataFrame rows
    for index, row in trades.iterrows():
        if row['transactionType'] == 'BUY':
            buy_qty += row['filledQty']
        elif row['transactionType'] == 'SELL':
            sell_qty += row['filledQty']

        # Check if total buy qty is equal to total sell qty
        if buy_qty == sell_qty:
            trade_count += 1
    return trade_count

def getProductType(product):
    prd = ''
    if product == 'I':
        prd = "INTRADAY"
    if product == 'M':
        prd = "MARGIN"
    if product == 'C':
        prd = "CNC"
    if product == 'F':
        prd = "MTF"
    if product == 'V':
        prd = "CO"
    if product == 'B':
        prd = "BO"
    return prd