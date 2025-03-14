from conf.config import nifty_fut_token
from utils.databaseHelper import db_helper
from schemas.dpSchema import DpSchema
import json
from sqlalchemy.orm import  Session
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime
from typing import List

class DecisionPoint:
    def __init__(self, name:str, price:float, call=True, put=True):
        self.name = name
        self.price = price
        self.call = call
        self.put = put
        self.date = datetime.now().date()

class DecisionPoints:
    def __init__(self):
        self.date = datetime.now().date()
        self.decisionPoints = []
        self.get_dps_from_db()

    def addDecisionPoint(self, price, name):
        # Check if a decisionPoint with the same name exists
        name = name.upper()
        flag = False
        for decisionPoint in self.decisionPoints:
            if decisionPoint.name == name and name != 'BRN':
                # Update the price if the decisionPoint exists
                decisionPoint.price = price
                flag = True
                break
            # if decisionPoint.price == price:
            #     # Update the price if the decisionPoint exists
            #     decisionPoint.name = name
            #     flag = True
            #     break
        # If it doesn't exist, create a new decisionPoint and add it to the list
        if not flag:
            decisionPoint = DecisionPoint(name, price)
            self.decisionPoints.append(decisionPoint)
        self.upload_dps_to_db()

        #TODO, check before placing the order
    def checkTradeValidity(self, price, type):
        '''
        check if price is close to an untraded decision point or not
        '''
        for decisionPoint in self.decisionPoints:
            if type == 'CALL' and decisionPoint.call and price >= decisionPoint.price and price - decisionPoint.price < 15:
                return True
            if type == 'PUT' and decisionPoint.put and price <= decisionPoint.price and decisionPoint.price - price  < 15:
                return True
        return False

    #TODO update after buy order is placed
    def updateDecisionPoints(self, price,  type):

        def find_closest_price(dps: List[DecisionPoint], target_price: float, above: bool) -> DecisionPoint:
            if above:
                dps = [dp for dp in dps if dp.price <= target_price]
            else:
                dps = [dp for dp in dps if dp.price >= target_price]

            closest_dp = min(dps, key=lambda item: abs(item.price - target_price))
            return closest_dp


        if type == 'CE' :
            closest_dp = find_closest_price(self.decisionPoints, price, True)
            closest_dp.call = False
        if type == 'PE':
            closest_dp = find_closest_price(self.decisionPoints, price, False)
            closest_dp.put = False

        self.upload_dps_to_db()

    def get_decision_points(self):
        # Convert list of DecisionPoint objects to list of dictionaries
        decision_points_dict = [
            {
                "name": dp.name,
                "price": dp.price,
                "call": dp.call,
                "put": dp.put
            } for dp in self.decisionPoints
        ]
        return decision_points_dict

    def upload_dps_to_db(self, db: Session = Depends(db_helper.get_db)):
        for dp in self.decisionPoints:
            db_helper.add_or_update_dp(dp)


    #TODO:
    def get_dps_from_db(self):
        dps = db_helper.get_dps(self.date)
        # dp_schemas = [DpSchema.from_orm(dp) for dp in dps]
        for dp in dps:
            decision_point = DecisionPoint(dp.name, dp.price, dp.call, dp.put)
            self.decisionPoints.append(decision_point)
        # return dps


decisionPoints = DecisionPoints()