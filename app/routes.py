from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import HistoricalData
from .indicators import moving_average
import pandas as pd

router = APIRouter()

def get_db():
    """
    Inicializa y cierra la sesión con la base de datos.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/historical-data/")
def read_historical_data(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Retorna datos históricos con soporte de paginación.
    """
    return db.query(HistoricalData).offset(skip).limit(limit).all()

@router.get("/moving-average/")
def get_moving_average(window: int, db: Session = Depends(get_db)):
    """
    Calcula y retorna la media móvil de los datos históricos.
    """
    data = db.query(HistoricalData).all()
    df = pd.DataFrame(data)
    return moving_average(df, window).tolist()