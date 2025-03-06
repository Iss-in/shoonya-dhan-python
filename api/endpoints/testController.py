from fastapi import APIRouter, HTTPException
from conf.config import dhan_api
from services.riskManagement import riskManagementobj
from services.tradeManagement import on_order_update
router = APIRouter()

@router.get("/api/placeOrder")
async def pnl():
    return dhan_api.order_placement(tradingsymbol="NIFTY 13 MAR 22150 PUT", exchange="NFO", quantity=150, price=0, trigger_price=0, order_type="MARKET", transaction_type="BUY",trade_type="MIS",  )


@router.get("/api/test")
async def brokerage():
    riskManagementobj.lockScreen()
    return 0

@router.get("/api/testOrder")
async def test_order_update():
    order_update = {'exchange': 'NSE', 'segment': 'D', 'source': 'T', 'securityId': '45463', 'clientId': '1103209581', 'exchOrderNo': '1000000017257919', 'orderNo': '10225030676527', 'product': 'I', 'txnType': 'B', 'orderType': 'LMT', 'validity': 'DAY', 'quantity': 150, 'tradedQty': 150, 'price': 188.1, 'tradedPrice': 188.1, 'avgTradedPrice': 188.1, 'offMktFlag': '0', 'orderDateTime': '2025-03-06 09:32:05', 'exchOrderTime': '2025-03-06 09:32:19', 'lastUpdatedTime': '2025-03-06 09:32:19', 'remarks': 'NR', 'mktType': 'NL', 'reasonDescription': 'TRADE CONFIRMED', 'legNo': 1, 'instrument': 'OPTIDX', 'symbol': 'NIFTY-Mar2025-2', 'productName': 'INTRADAY', 'status': 'Traded', 'lotSize': 75, 'strikePrice': 22400, 'expiryDate': '2025-03-13', 'optType': 'PE', 'displayName': 'NIFTY 13 MAR 22400 PUT', 'isin': 'NA', 'series': 'XX', 'goodTillDaysDate': '2025-03-06', 'refLtp': 192.35, 'tickSize': 0.05, 'algoId': '0', 'multiplier': 1}

    order = {"Data" : order_update }
    on_order_update(order)
    # dhan_api.Dhan.place_order("45463", "NSE_FNO", "SELL", 75, "STOP_LOSS", "INTRADAY", 100, 100.2, )