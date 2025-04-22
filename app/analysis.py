import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import json
from app.indicators import moving_average, exponential_moving_average, relative_strength_index, bollinger_bands, macd
from app.DB.DataBase import get_db_connection, engine
from sqlalchemy import text

def analyze_ticker(ticker, data=None, period='1y'):
    """
    Perform comprehensive analysis on a ticker
    
    Args:
        ticker (str): The ticker symbol
        data (pandas.DataFrame, optional): The data to analyze. If None, data will be fetched from the database.
        period (str): The period to analyze
    
    Returns:
        dict: Analysis results
    """
    if data is None:
        # Fetch data from database
        query = "SELECT * FROM prices WHERE Ticker = :ticker ORDER BY Date"
        with engine.connect() as conn:
            result = conn.execute(text(query), {'ticker': ticker})
            data = pd.DataFrame(result.fetchall())
        
        if data.empty:
            return {"error": f"No data found for {ticker}"}
    
    # Ensure we have the right column names
    if 'Close' not in data.columns and 'close' in data.columns:
        data['Close'] = data['close']
    if 'Open' not in data.columns and 'open' in data.columns:
        data['Open'] = data['open']
    if 'High' not in data.columns and 'high' in data.columns:
        data['High'] = data['high']
    if 'Low' not in data.columns and 'low' in data.columns:
        data['Low'] = data['low']
    if 'Volume' not in data.columns and 'volume' in data.columns:
        data['Volume'] = data['volume']
    
    # Basic statistics
    stats = {
        'ticker': ticker,
        'start_date': data['Date'].min() if 'Date' in data.columns else data.index.min(),
        'end_date': data['Date'].max() if 'Date' in data.columns else data.index.max(),
        'days': len(data),
        'current_price': float(data['Close'].iloc[-1]),
        'change_percent': float(((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100),
        'min_price': float(data['Low'].min()),
        'max_price': float(data['High'].max()),
        'avg_volume': float(data['Volume'].mean()),
        'volatility': float(data['Close'].pct_change().std() * 100)  # Daily volatility in percentage
    }
    
    # Generate plots
    plots = {
        'price_chart': plot_price_chart(data, ticker),
        'volume_chart': plot_volume_chart(data, ticker),
        'ma_chart': plot_moving_averages(data, ticker),
        'rsi_chart': plot_rsi(data, ticker),
        'bollinger_chart': plot_bollinger_bands(data, ticker),
        'macd_chart': plot_macd(data, ticker)
    }
    
    return {
        'stats': stats,
        'plots': plots
    }

def analyze_correlation(tickers, period='1y'):
    """
    Analyze correlation between multiple tickers
    
    Args:
        tickers (list): List of ticker symbols
        period (str): The period to analyze
    
    Returns:
        dict: Correlation analysis results
    """
    # Fetch data for all tickers
    all_data = {}
    for ticker in tickers:
        query = "SELECT Date, Close FROM prices WHERE Ticker = :ticker ORDER BY Date"
        with engine.connect() as conn:
            result = conn.execute(text(query), {'ticker': ticker})
            data = pd.DataFrame(result.fetchall())
        
        if not data.empty:
            all_data[ticker] = data.set_index('Date')['Close']
    
    if not all_data:
        return {"error": "No data found for the specified tickers"}
    
    # Create a DataFrame with all close prices
    df = pd.DataFrame(all_data)
    
    # Calculate correlation matrix
    corr_matrix = df.corr().round(2)
    
    # Generate correlation heatmap
    plt.figure(figsize=(10, 8))
    plt.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar(label='Correlation')
    plt.xticks(range(len(corr_matrix.columns)), corr_matrix.columns, rotation=45)
    plt.yticks(range(len(corr_matrix.columns)), corr_matrix.columns)
    
    # Add correlation values to the heatmap
    for i in range(len(corr_matrix.columns)):
        for j in range(len(corr_matrix.columns)):
            plt.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}', 
                     ha='center', va='center', color='white' if abs(corr_matrix.iloc[i, j]) > 0.5 else 'black')
    
    plt.title('Correlation Matrix')
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    heatmap_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Generate price comparison chart
    plt.figure(figsize=(12, 6))
    
    # Normalize prices to start at 100 for comparison
    normalized_df = df.div(df.iloc[0]) * 100
    
    for ticker in normalized_df.columns:
        plt.plot(normalized_df.index, normalized_df[ticker], label=ticker)
    
    plt.title('Price Comparison (Normalized)')
    plt.xlabel('Date')
    plt.ylabel('Normalized Price (Base 100)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    comparison_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return {
        'correlation_matrix': corr_matrix.to_dict(),
        'heatmap': f'data:image/png;base64,{heatmap_img}',
        'price_comparison': f'data:image/png;base64,{comparison_img}'
    }

def plot_price_chart(data, ticker):
    """Generate a price chart for a ticker"""
    plt.figure(figsize=(12, 6))
    
    date_col = 'Date' if 'Date' in data.columns else data.index
    
    plt.plot(date_col, data['Close'], label='Close Price')
    plt.title(f'{ticker} Price Chart')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def plot_volume_chart(data, ticker):
    """Generate a volume chart for a ticker"""
    plt.figure(figsize=(12, 6))
    
    date_col = 'Date' if 'Date' in data.columns else data.index
    
    plt.bar(date_col, data['Volume'], alpha=0.7, color='blue')
    plt.title(f'{ticker} Volume Chart')
    plt.xlabel('Date')
    plt.ylabel('Volume')
    plt.grid(True, alpha=0.3)
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def plot_moving_averages(data, ticker):
    """Generate a chart with moving averages"""
    plt.figure(figsize=(12, 6))
    
    date_col = 'Date' if 'Date' in data.columns else data.index
    
    plt.plot(date_col, data['Close'], label='Close Price')
    plt.plot(date_col, moving_average(data, 20), label='MA(20)')
    plt.plot(date_col, moving_average(data, 50), label='MA(50)')
    plt.plot(date_col, moving_average(data, 200), label='MA(200)')
    
    plt.title(f'{ticker} Moving Averages')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def plot_rsi(data, ticker, window=14):
    """Generate an RSI chart"""
    plt.figure(figsize=(12, 6))
    
    date_col = 'Date' if 'Date' in data.columns else data.index
    rsi = relative_strength_index(data, window)
    
    plt.plot(date_col, rsi, label=f'RSI({window})')
    plt.axhline(y=70, color='r', linestyle='-', alpha=0.3)
    plt.axhline(y=30, color='g', linestyle='-', alpha=0.3)
    plt.title(f'{ticker} Relative Strength Index')
    plt.xlabel('Date')
    plt.ylabel('RSI')
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def plot_bollinger_bands(data, ticker, window=20, num_std=2):
    """Generate a Bollinger Bands chart"""
    plt.figure(figsize=(12, 6))
    
    date_col = 'Date' if 'Date' in data.columns else data.index
    ma, upper, lower = bollinger_bands(data, window, num_std)
    
    plt.plot(date_col, data['Close'], label='Close Price')
    plt.plot(date_col, ma, label=f'MA({window})')
    plt.plot(date_col, upper, label='Upper Band')
    plt.plot(date_col, lower, label='Lower Band')
    plt.fill_between(date_col, upper, lower, alpha=0.1)
    
    plt.title(f'{ticker} Bollinger Bands')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def plot_macd(data, ticker, fast=12, slow=26, signal=9):
    """Generate a MACD chart"""
    plt.figure(figsize=(12, 8))
    
    date_col = 'Date' if 'Date' in data.columns else data.index
    macd_line, signal_line, histogram = macd(data, fast, slow, signal)
    
    plt.subplot(2, 1, 1)
    plt.plot(date_col, data['Close'], label='Close Price')
    plt.title(f'{ticker} Price and MACD')
    plt.ylabel('Price')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(date_col, macd_line, label='MACD Line')
    plt.plot(date_col, signal_line, label='Signal Line')
    plt.bar(date_col, histogram, label='Histogram', alpha=0.3)
    plt.axhline(y=0, color='k', linestyle='-', alpha=0.2)
    plt.title('MACD')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'
