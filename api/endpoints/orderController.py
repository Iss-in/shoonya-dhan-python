from fastapi import APIRouter, HTTPException, Request
from services.riskManagement import *
from services.tradeManagement import updateTargets, tradeManager
from services.orderManagement import buyOrder, modifyActiveOrder
from typing import List, Optional
from pydantic import BaseModel
from typing import Dict, Any
from conf.config import shoonya_api
router = APIRouter()

class TargetRequest(BaseModel):
    t1: float
    t2: float
    t3: float


@router.post("/api/updateTargets", response_model=Dict[str, Any])
async def update_targets(target_data: TargetRequest):
    try:
        # Extract target values from the request
        t1 = target_data.t1
        t2 = target_data.t2
        t3 = target_data.t3

        # Process the target updates
        targets = {"t1":t1, "t2":t2, "t3":t3}
        result = updateTargets(targets)

        if result:
            return {"success": True, "message": "Your targets have been successfully updated."}
        else:
            raise HTTPException(status_code=500, detail="Failed to update targets")
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Error updating targets: {str(e)}")


@router.post("/api/buyOrder/{token}/{priceType}/{price}")
async def buy_order(token: str, priceType: str, price: float):
    try:
        # Call the service method (assumes a similar function exists in your module)
        if tradeManager.ltps[token] < price:
            price = tradeManager.ltps[token]

        buyOrder(token, priceType, price)
        shoonya_api.subscribe("NFO|" + str(token))
        # You can process 'res' if needed; here we simply return a success message.
        return {"message": "order placed"}
    except Exception as e:
        # Raise an HTTPException if there's an error in processing the order
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/cancelOrder/{orderId}")
async def buy_order(orderId: int):
    return dhan_api.cancel_order(orderId)

@router.post("/api/modifyOrder/{orderId}/{newPrice}")
async def modifyOrder(orderId: int, newPrice: float):
    return modifyActiveOrder(orderId, newPrice)