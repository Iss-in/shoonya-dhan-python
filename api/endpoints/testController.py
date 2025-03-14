from fastapi import APIRouter, HTTPException
from conf.config import dhan_api
from services.riskManagement import riskManagementobj
from services.tradeManagement import on_order_update, updateOpenOrders, createTrade
from pydantic import BaseModel
from conf import websocketService
import random
from datetime import datetime
router = APIRouter()
from models.DecisionPoints import decisionPoints

@router.get("/api/placeOrder")
async def pnl():
    return dhan_api.order_placement(tradingsymbol="NIFTY 13 MAR 22150 PUT", exchange="NFO", quantity=150, price=0, trigger_price=0, order_type="MARKET", transaction_type="BUY",trade_type="MIS",  )


@router.get("/api/test")
async def brokerage():
    riskManagementobj.lockScreen()
    return 0



class QuoteResponse(BaseModel):
    quote: str


@router.get("/api/quote", response_model=QuoteResponse)
async def quote():
    return QuoteResponse(quote="just fucking follow the rules")



@router.get("/api/testOrder")
async def test_order_update():
    order_update = {'exchange': 'NSE', 'segment': 'D', 'source': 'P', 'securityId': '45471', 'clientId': '1103209581', 'exchOrderNo': '1300000005880874', 'orderNo': '3225031246227', 'product': 'I', 'txnType': 'S', 'orderType': 'SL', 'validity': 'DAY', 'remainingQuantity': 75, 'quantity': 75, 'price': 131, 'triggerPrice': 131.2, 'offMktFlag': '0', 'orderDateTime': '2025-03-12 09:27:30', 'exchOrderTime': '2025-03-12 09:27:30', 'lastUpdatedTime': '2025-03-12 09:27:30', 'remarks': 'NR', 'mktType': 'NL', 'reasonDescription': 'CONFIRMED', 'legNo': 1, 'instrument': 'OPTIDX', 'symbol': 'NIFTY-Mar2025-2', 'productName': 'INTRADAY', 'status': 'Modified', 'lotSize': 75, 'strikePrice': 22550, 'expiryDate': '2025-03-13', 'optType': 'PE', 'displayName': 'NIFTY 13 MAR 22550 PUT', 'isin': 'NA', 'series': 'XX', 'goodTillDaysDate': '2025-03-12', 'refLtp': 133.2, 'tickSize': 0.05, 'algoId': '0', 'multiplier': 1}

    order = {"Data" : order_update }
    on_order_update(order)
    # createTrade(45472, order_update)
    # dhan_api.Dhan.place_or
    # der("45463", "NSE_FNO", "SELL", 75, "STOP_LOSS", "INTRADAY", 100, 100.2, )

@router.get("/api/modifyOrder")
async def modifyOrder():
    # ret = dhan_api.Dhan.modify_order(order_id="12250307294127", order_type="LIMIT", quantity=75,
    #                                  price=101)
    ret = dhan_api.Dhan.modify_order( order_id=22250307395227, order_type="LIMIT", leg_name="ENTRY_LEG",  quantity=75,
                                      price=160, trigger_price=0, disclosed_quantity=0, validity='DAY')

    print(ret)

@router.get("/api/getGreek")
async def getGreek():
    ret = dhan_api.get_option_greek(22500, 0, "NIFTY", 7, "delta", "CE")
    print(ret)

    # def get_option_greek(self, strike: int, expiry: int, asset: str, interest_rate: float, flag: str, scrip_type: str):


@router.get("/api/sampleFeed")
async def getGreek():
    epoch = int(datetime.now().timestamp())
    websocketService.send_price_feed("45467", epoch, 100* random.random())
    websocketService.send_price_feed("45475", epoch, 100* random.random())


@router.get("/api/toast")
async def getGreek():
    websocketService.send_toast("hello", "world")

@router.post("/api/addDp/{price}/{name}")
async def getGreek(price:int, name:str):
    decisionPoints.addDecisionPoint(price, name)

@router.post("/api/testDp/{price}/{type}")
async def getGreek(price:int, type:str):
    decisionPoints.updateDecisionPoints(price, type)


@router.get("/api/orderUpdate")
async def getGreek():
    updateOpenOrders()