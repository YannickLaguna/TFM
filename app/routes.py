from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import HistoricalData
from .indicators import moving_average
import pandas as pd

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/historical-data/")
def read_historical_data(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(HistoricalData).offset(skip).limit(limit).all()

@router.get("/moving-average/")
def get_moving_average(window: int, db: Session = Depends(get_db)):
    data = db.query(HistoricalData).all()
    df = pd.DataFrame(data)
    return moving_average(df, window).tolist()
