import os
import sqlite3
import yfinance as yf
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Create data directory if it doesn't exist
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
os.makedirs(data_dir, exist_ok=True)

# SQLite database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'TFM.db')
URL_DATABASE = f'sqlite:///{DB_PATH}'

# Create the engine and session with SQLAlchemy
engine = create_engine(URL_DATABASE, echo=False)
Session = sessionmaker(engine)
Base = declarative_base()

def get_db_connection():
    """Create a SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initialize the database with required tables"""
    # Create tables using SQLAlchemy
    Base.metadata.create_all(bind=engine)
    
    # Create prices table if it doesn't exist
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prices (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Date DATE,
                Open FLOAT,
                High FLOAT,
                Low FLOAT,
                Close FLOAT,
                Volume INTEGER,
                Ticker VARCHAR(255)
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS strategies (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name VARCHAR(255),
                Code VARCHAR(255),
                Description TEXT,
                Parameters TEXT
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                StrategyID INTEGER,
                Ticker VARCHAR(255),
                StartDate DATE,
                EndDate DATE,
                InitialCapital FLOAT,
                FinalCapital FLOAT,
                Returns FLOAT,
                SharpeRatio FLOAT,
                MaxDrawdown FLOAT,
                FOREIGN KEY (StrategyID) REFERENCES strategies(ID)
            );
        """))
    
    print("Database initialized successfully")

def fetch_and_store_data(ticker, start_date='2020-01-01', end_date='2023-01-01'):
    """Fetch data from yfinance and store it in the database"""
    # Download data
    data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
    
    # Prepare records for insertion
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
    
    # Insert data into the database
    query = """INSERT INTO prices (Date, Open, High, Low, Close, Volume, Ticker)
               VALUES (:date, :open, :high, :low, :close, :volume, :ticker)"""
    
    with engine.begin() as conn:
        conn.execute(text(query), records)
    
    print(f"Data for {ticker} inserted successfully")
    return data

def get_ticker_data(ticker, start_date=None, end_date=None):
    """Retrieve data for a specific ticker from the database"""
    query = "SELECT * FROM prices WHERE Ticker = :ticker"
    params = {'ticker': ticker}
    
    if start_date:
        query += " AND Date >= :start_date"
        params['start_date'] = start_date
    
    if end_date:
        query += " AND Date <= :end_date"
        params['end_date'] = end_date
    
    query += " ORDER BY Date"
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()
    
    if not rows:
        # If no data in database, fetch it
        return fetch_and_store_data(ticker, start_date, end_date)
    
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    return df

# Initialize database when module is imported
initialize_database()
