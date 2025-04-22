from pydantic import BaseModel
from datetime import date
from typing import Optional

class HistoricalDataModel(BaseModel):
    id: Optional[int]
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    ticker: str

class StrategyModel(BaseModel):
    id: Optional[int]
    name: str
    code: str
    description: str
    parameters: str

class BacktestResultModel(BaseModel):
    id: Optional[int]
    strategy_id: int
    ticker: str
    start_date: date
    end_date: date
    initial_capital: float
    final_capital: float
    returns: float
    sharpe_ratio: float
    max_drawdown: float