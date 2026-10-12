from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)


class BacktestResult(Base):
    __tablename__ = "backtests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    stats_json = Column(Text)
    trades_json = Column(Text)
    notes = Column(String, nullable=True)


class SignalLog(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    signal = Column(Integer)
    confidence = Column(Float)
    price = Column(Float)
    user_id = Column(Integer, nullable=True)
