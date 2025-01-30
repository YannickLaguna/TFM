from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import yfinance as yf
import pandas as pd
import psycopg2
from psycopg2 import sql

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Conexión a la base de datos PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        dbname='tfm_db',
        user='postgres',
        password='lzPostgre00',
        host='127.0.0.1',  # Puedes usar '127.0.0.1' si la base de datos está en tu máquina local
        port='5432'
    )
    return conn

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/data/{ticker}")
async def get_data(ticker: str):
    # Obtener datos históricos
    datos = yf.Ticker(ticker).history(period='1mo')
    
    # Volcar datos en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla si no existe
    cursor.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {} (
            fecha DATE PRIMARY KEY,
            apertura REAL,
            cierre REAL,
            alto REAL,
            bajo REAL,
            volumen INTEGER
        )
    """).format(sql.Identifier(ticker)))
    
    # Insertar o actualizar datos
    for index, row in datos.iterrows():
        cursor.execute(sql.SQL("""
            INSERT INTO {} (fecha, apertura, cierre, alto, bajo, volumen)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (fecha) DO UPDATE SET
                apertura = EXCLUDED.apertura,
                cierre = EXCLUDED.cierre,
                alto = EXCLUDED.alto,
                bajo = EXCLUDED.bajo,
                volumen = EXCLUDED.volumen
        """).format(sql.Identifier(ticker)), (index.date(), row['Open'], row['Close'], row['High'], row['Low'], row['Volume']))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return datos.reset_index().to_dict(orient='records')

@app.get("/historico/{ticker}")
async def get_historico(ticker: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(ticker)))
    datos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{"fecha": row[0], "apertura": row[1], "cierre": row[2], "alto": row[3], "bajo": row[4], "volumen": row[5]} for row in datos]
