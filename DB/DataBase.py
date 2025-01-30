# -*- coding: utf-8 -*-
import psycopg2
import yfinance as yf
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
psycopg2.extensions.register_adapter(np.int64, psycopg2._psycopg.AsIs)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


URL_DATABASE = 'postgresql://postgres:lzPostgre00@localhost:5432/tfm_db'

# Crear el motor y sesión con SQLAlchemy
engine = create_engine(URL_DATABASE, echo= True)
Session = sessionmaker(engine)
Base = declarative_base() # ns 

# DATA
## yfinance
import yfinance as yf
ticker = 'AAPL'  # Ejemplo de ticker
data = yf.download(ticker, start='2020-01-01', end='2023-01-01',auto_adjust=False)
print(data)
# Creando el cursor/pointer
conn = psycopg2.connect(
    database="tfm_db", user='postgres', password='lzPostgre00', host='127.0.0.1', port='5432'
)
cursor = conn.cursor()

    # Crear tabla precios
##TODO pensar ID
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS prices (
            ID serial PRIMARY KEY,
            Date DATE,
            Open FLOAT,
            High FLOAT,
            Low FLOAT,
            Close FLOAT,
            Volume BIGINT,
            Ticker VARCHAR(255)
        );
    """))
    print("Tabla creada exitosamente")


# Volcado de datos
query = """INSERT INTO prices (Date, Open, High, Low, Close, Volume, Ticker)
           VALUES (:date, :open, :high, :low, :close, :volume, :ticker)"""

# Crear registros
records = [
    {
        'date': index.date(),
        'open': float(row['Open']),
        'high': float(row['High']),
        'low': float(row['Low']),
        'close': float(row['Close']),
        'volume': int(row['Volume']),
        'ticker': ticker
    }
    for index, row in data.iterrows()
]

# Usar una nueva conexión para insertar los datos
with engine.begin() as conn:
    conn.execute(text(query), records)
    print("Datos insertados exitosamente")

    # Test de consulta
with engine.begin() as conn:
    result = conn.execute(text("SELECT * FROM prices"))
    for row in result:
        print(row)

# finally:
if conn:
    cursor.close()
    conn.close()
