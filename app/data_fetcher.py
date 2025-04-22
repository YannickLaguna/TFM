import yfinance as yf
import pandas as pd
import os
from app.DB.DataBase import get_db_connection, engine
from sqlalchemy import text


def fetch_ticker_data(ticker, period, interval):
    """
    Descarga los datos financieros de un símbolo utilizando Yahoo Finance.

    Parámetros
    ----------
    ticker : str
        Símbolo bursátil (por ejemplo, 'AAPL').
    period : str
        Periodo de tiempo a descargar (por ejemplo, '1mo', '1y', 'max').
    interval : str
        Intervalo entre los puntos de datos (por ejemplo, '1d', '1wk').

    Returns
    -------
    pandas.DataFrame
        Devuelve un DataFrame con los datos descargados, o None si ocurren errores
        o si el DataFrame se encuentra vacío.
    """
    try:
        data = yf.download(ticker, period=period, interval=interval, auto_adjust=True)
        if data.empty:
            return None

        # Almacenar datos en la base de datos
        store_ticker_data(ticker, data)
        
        return data
    except Exception as e:
        print(f"Error al obtener datos para {ticker}: {e}")
        return None

def store_ticker_data(ticker, data):
    """
    Store ticker data in the database
    
    Args:
        ticker (str): The ticker symbol
        data (pandas.DataFrame): The data to store
    """
    # Reset index to get Date as a column
    data_with_date = data.reset_index()
    
    # Print the columns to understand the structure
    print(data_with_date.columns)
    
    # Check if the DataFrame has a MultiIndex for columns
    if isinstance(data_with_date.columns, pd.MultiIndex):
        # Access columns using the correct level
        data_flat = pd.DataFrame()
        data_flat['Date'] = data_with_date[('Date', '')]
        data_flat['Open'] = data_with_date[('Open', ticker)]
        data_flat['High'] = data_with_date[('High', ticker)]
        data_flat['Low'] = data_with_date[('Low', ticker)]
        data_flat['Close'] = data_with_date[('Close', ticker)]
        data_flat['Volume'] = data_with_date[('Volume', ticker)]
    else:
        # If the DataFrame does not have a MultiIndex, use the columns directly
        data_flat = data_with_date[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    # Convert DataFrame to dictionary records
    dict_records = data_flat.to_dict('records')
    
    # Prepare records for insertion with proper type conversion
    records = []
    for row in dict_records:
        date_val = row['Date']
        date_val = date_val.date() if hasattr(date_val, 'date') else date_val
        
        record = {
            'date': date_val,
            'open': float(row['Open']) if pd.notna(row['Open']) else None,
            'high': float(row['High']) if pd.notna(row['High']) else None,
            'low': float(row['Low']) if pd.notna(row['Low']) else None,
            'close': float(row['Close']) if pd.notna(row['Close']) else None,
            'volume': int(row['Volume']) if pd.notna(row['Volume']) else None,
            'ticker': ticker
        }
        records.append(record)
    
    # Insert data into the database
    query = """INSERT OR REPLACE INTO prices (Date, Open, High, Low, Close, Volume, Ticker)
               VALUES (:date, :open, :high, :low, :close, :volume, :ticker)"""
    
    try:
        with engine.begin() as conn:
            conn.execute(text(query), records)
        return True
    except Exception as e:
        print(f"Error al almacenar datos para {ticker}: {e}")
        # Para depuración, imprime más información sobre el error
        import traceback
        traceback.print_exc()
        return False
    
def get_available_tickers():
    """
    Get a list of all tickers available in the database
    
    Returns:
        list: List of ticker symbols
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Ticker FROM prices")
    tickers = [row['Ticker'] for row in cursor.fetchall()]
    conn.close()
    
    return tickers

def get_ticker_data_from_db(ticker, start_date=None, end_date=None):
    """
    Get data for a ticker from the database
    
    Args:
        ticker (str): The ticker symbol
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    
    Returns:
        pandas.DataFrame: The data from the database
    """
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
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    return df
