from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Date, String, Float, Boolean, create_engine

Base = declarative_base()

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    plan = Column(String, nullable=False)

class Dp(Base):
    __tablename__ = "decision_points"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    call = Column(Boolean, nullable=False)
    put = Column(Boolean, nullable=False)