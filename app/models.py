from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.DB.DataBase import Base

class HistoricalData(Base):
    __tablename__ = "prices"

    ID = Column(Integer, primary_key=True)
    Date = Column(Date, index=True)
    Open = Column(Float)
    High = Column(Float)
    Low = Column(Float)
    Close = Column(Float)
    Volume = Column(Integer)
    Ticker = Column(String(255))

class Strategy(Base):
    __tablename__ = "strategies"

    ID = Column(Integer, primary_key=True)
    Name = Column(String(255))
    Code = Column(String(255))
    Description = Column(Text)
    Parameters = Column(Text)
    
    backtest_results = relationship("BacktestResult", back_populates="strategy")

class BacktestResult(Base):
    __tablename__ = "backtest_results"

    ID = Column(Integer, primary_key=True)
    StrategyID = Column(Integer, ForeignKey("strategies.ID"))
    Ticker = Column(String(255))
    StartDate = Column(Date)
    EndDate = Column(Date)
    InitialCapital = Column(Float)
    FinalCapital = Column(Float)
    Returns = Column(Float)
    SharpeRatio = Column(Float)
    MaxDrawdown = Column(Float)
    
    strategy = relationship("Strategy", back_populates="backtest_results")
