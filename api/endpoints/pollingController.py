from fastapi import APIRouter, HTTPException, Query, Depends
from conf.config import dhan_api
from services.optionUpdate import optionUpdateObj
from services.tradeManagement import on_order_update, updateOpenOrders
from pydantic import BaseModel
from schemas.planSchema import PlanSchema
from models.DecisionPoints import decisionPoints
from datetime import date
from utils.databaseHelper import db_helper
from sqlalchemy.orm import sessionmaker, Session
from conf.config import logger
from typing import Dict

router = APIRouter()

@router.post("/api/firstFetch")
async def firstFetch():
    optionUpdateObj.updateOptions(firstFetch=True)
    updateOpenOrders()

@router.get("/api/margin")
async def getMargin():
    return dhan_api.get_balance()


@router.get("/api/getDps")
async def getDps():
    return decisionPoints.get_decision_points()


class TradePlanRequest(BaseModel):
    date: date

class TradePlanUpdate(BaseModel):
    plan: str
@router.get("/api/tradePlan")
def get_plan(date: date, db: Session = Depends(db_helper.get_db)) -> Dict[str, str]:
    try:
        date = date.strftime("%Y-%m-%d")
        return db_helper.get_plan(db, date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/tradePlan", response_model=PlanSchema)
def create_or_update_plan(plan: PlanSchema, db: Session = Depends(db_helper.get_db)):
    try:
        db_plan = db_helper.add_or_update_plan(db, plan)
        return db_plan
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))








