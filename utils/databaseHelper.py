from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from models.models import Plan, Dp
DATABASE_URL = "postgresql://user:password@100.115.108.27:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBHelper:
    def __init__(self):
        self.db = SessionLocal()

    def get_db(self):
        try:
            yield self.db
        finally:
            self.db.close()

    def add_or_update_plan(self, db: Session, plan_schema):
        plan = db.query(Plan).filter(Plan.date == plan_schema.date).first()
        if plan:
            plan.plan = plan_schema.plan
        else:
            plan = Plan(date=plan_schema.date, plan=plan_schema.plan)
            db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    def add_or_update_dp(self, dp_schema):
        db = self.db
        dp = db.query(Dp).filter(Dp.date == dp_schema.date).filter(Dp.name == dp_schema.name).first()
        if dp:
            dp.price = dp_schema.price
            dp.call = dp_schema.call
            dp.put = dp_schema.put
        else:
            dp = Dp(date=dp_schema.date, name=dp_schema.name, price=dp_schema.price, call=dp_schema.call, put=dp_schema.put)
            db.add(dp)
        db.commit()
        db.refresh(dp)
        return dp

    def get_dps(self, date):
        db = self.db
        dps = db.query(Dp).filter(Dp.date == date).all()
        return dps

    def get_plan(self, db: Session, date):
        plan = db.query(Plan).filter(Plan.date == date).first()
        if plan:
            return {"date": date, "plan": plan.plan}
        else:
            return {"date": date, "plan": "no plan for this day"}

# Example usage with FastAPI
from fastapi import FastAPI, Depends, HTTPException

# app = FastAPI()
db_helper = DBHelper()

