from fastapi import APIRouter, HTTPException
from services.riskManagement import *
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()



@router.get("/api/pnl")
async def pnl():
    return riskManagementobj.pnl

@router.get("/api/killswitch")
async def killswitch():
    return riskManagementobj.killswitch()
