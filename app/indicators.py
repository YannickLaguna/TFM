import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

def moving_average(data, window):
    """Calculate the moving average for a given window"""
    if 'Close' in data.columns:
        return data['Close'].rolling(window=window).mean()
    elif 'close' in data.columns:
        return data['close'].rolling(window=window).mean()
    else:
        raise ValueError("Data must contain 'Close' or 'close' column")

def exponential_moving_average(data, window):
    """Calculate the exponential moving average for a given window"""
    if 'Close' in data.columns:
        return data['Close'].ewm(span=window, adjust=False).mean()
    elif 'close' in data.columns:
        return data['close'].ewm(span=window, adjust=False).mean()
    else:
        raise ValueError("Data must contain 'Close' or 'close' column")

def relative_strength_index(data, window=14):
    """Calculate the RSI for a given window"""
    close_column = 'Close' if 'Close' in data.columns else 'close'
    delta = data[close_column].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def bollinger_bands(data, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    close_column = 'Close' if 'Close' in data.columns else 'close'
    ma = data[close_column].rolling(window=window).mean()
    std = data[close_column].rolling(window=window).std()
    
    upper_band = ma + (std * num_std)
    lower_band = ma - (std * num_std)
    
    return ma, upper_band, lower_band

def macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    close_column = 'Close' if 'Close' in data.columns else 'close'
    exp1 = data[close_column].ewm(span=fast, adjust=False).mean()
    exp2 = data[close_column].ewm(span=slow, adjust=False).mean()
    
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def plot_indicator(data, indicator_name, **kwargs):
    """Generate a plot for a specific indicator"""
    plt.figure(figsize=(12, 6))
    
    close_column = 'Close' if 'Close' in data.columns else 'close'
    date_column = 'Date' if 'Date' in data.columns else data.index
    
    if indicator_name == 'moving_average':
        window = kwargs.get('window', 20)
        ma = moving_average(data, window)
        plt.plot(date_column, data[close_column], label='Price')
        plt.plot(date_column, ma, label=f'MA({window})')
        plt.title(f'Moving Average ({window} periods)')
        
    elif indicator_name == 'ema':
        window = kwargs.get('window', 20)
        ema = exponential_moving_average(data, window)
        plt.plot(date_column, data[close_column], label='Price')
        plt.plot(date_column, ema, label=f'EMA({window})')
        plt.title(f'Exponential Moving Average ({window} periods)')
        
    elif indicator_name == 'rsi':
        window = kwargs.get('window', 14)
        rsi = relative_strength_index(data, window)
        plt.plot(date_column, rsi, label=f'RSI({window})')
        plt.axhline(y=70, color='r', linestyle='-', alpha=0.3)
        plt.axhline(y=30, color='g', linestyle='-', alpha=0.3)
        plt.title(f'Relative Strength Index ({window} periods)')
        plt.ylim(0, 100)
        
    elif indicator_name == 'bollinger':
        window = kwargs.get('window', 20)
        num_std = kwargs.get('num_std', 2)
        ma, upper, lower = bollinger_bands(data, window, num_std)
        plt.plot(date_column, data[close_column], label='Price')
        plt.plot(date_column, ma, label=f'MA({window})')
        plt.plot(date_column, upper, label='Upper Band')
        plt.plot(date_column, lower, label='Lower Band')
        plt.fill_between(date_column, upper, lower, alpha=0.1)
        plt.title(f'Bollinger Bands ({window} periods, {num_std} std)')
        
    elif indicator_name == 'macd':
        fast = kwargs.get('fast', 12)
        slow = kwargs.get('slow', 26)
        signal = kwargs.get('signal', 9)
        macd_line, signal_line, histogram = macd(data, fast, slow, signal)
        
        plt.subplot(2, 1, 1)
        plt.plot(date_column, data[close_column], label='Price')
        plt.title(f'Price and MACD ({fast}, {slow}, {signal})')
        plt.legend()
        
        plt.subplot(2, 1, 2)
        plt.plot(date_column, macd_line, label='MACD Line')
        plt.plot(date_column, signal_line, label='Signal Line')
        plt.bar(date_column, histogram, label='Histogram', alpha=0.3)
        plt.axhline(y=0, color='k', linestyle='-', alpha=0.2)
        plt.title('MACD')
        
    else:
        plt.text(0.5, 0.5, f"Indicator '{indicator_name}' not implemented", 
                 horizontalalignment='center', verticalalignment='center')
    
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
