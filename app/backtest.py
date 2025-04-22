import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import json
from app.DB.DataBase import get_db_connection, engine
from sqlalchemy import text

def create_strategy(name, code, description, parameters):
    """
    Create a new trading strategy in the database
    
    Args:
        name (str): Strategy name
        code (str): Strategy code identifier
        description (str): Strategy description
        parameters (dict): Strategy parameters
    
    Returns:
        int: Strategy ID
    """
    # Convert parameters dict to JSON string
    params_json = json.dumps(parameters)
    
    # Insert strategy into database
    query = """
    INSERT INTO strategies (Name, Code, Description, Parameters)
    VALUES (:name, :code, :description, :parameters)
    """
    
    with engine.begin() as conn:
        result = conn.execute(
            text(query), 
            {'name': name, 'code': code, 'description': description, 'parameters': params_json}
        )
    
    # Get the ID of the inserted strategy
    query = "SELECT ID FROM strategies WHERE Code = :code ORDER BY ID DESC LIMIT 1"
    with engine.connect() as conn:
        result = conn.execute(text(query), {'code': code})
        strategy_id = result.fetchone()[0]
    
    return strategy_id

def get_strategy(strategy_id=None, code=None):
    """
    Get a strategy from the database
    
    Args:
        strategy_id (int, optional): Strategy ID
        code (str, optional): Strategy code
    
    Returns:
        dict: Strategy details
    """
    if strategy_id is not None:
        query = "SELECT * FROM strategies WHERE ID = :id"
        params = {'id': strategy_id}
    elif code is not None:
        query = "SELECT * FROM strategies WHERE Code = :code"
        params = {'code': code}
    else:
        return None
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        strategy = result.fetchone()
    
    if not strategy:
        return None
    
    # Convert row to dict
    strategy_dict = dict(strategy)
    
    # Parse parameters JSON
    if strategy_dict['Parameters']:
        strategy_dict['Parameters'] = json.loads(strategy_dict['Parameters'])
    
    return strategy_dict

def get_all_strategies():
    """
    Get all strategies from the database
    
    Returns:
        list: List of strategy dictionaries
    """
    query = "SELECT * FROM strategies"
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        strategies = result.fetchall()
    
    # Convert rows to dicts and parse parameters JSON
    strategy_list = []
    for strategy in strategies:
        strategy_dict = dict(strategy)
        if strategy_dict['Parameters']:
            strategy_dict['Parameters'] = json.loads(strategy_dict['Parameters'])
        strategy_list.append(strategy_dict)
    
    return strategy_list

def run_backtest(strategy_id, ticker, start_date=None, end_date=None, initial_capital=10000, commission=0.001):
    """
    Run a backtest for a strategy on a ticker
    
    Args:
        strategy_id (int): Strategy ID
        ticker (str): Ticker symbol
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        initial_capital (float): Initial capital
        commission (float): Commission rate
    
    Returns:
        dict: Backtest results
    """
    # Get strategy details
    strategy = get_strategy(strategy_id)
    if not strategy:
        return {"error": f"Strategy with ID {strategy_id} not found"}
    
    # Get ticker data
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
        data = pd.DataFrame(result.fetchall())
    
    if data.empty:
        return {"error": f"No data found for {ticker}"}
    
    # Run the appropriate strategy
    if strategy['Code'] == 'moving_average_crossover':
        results = backtest_ma_crossover(data, strategy['Parameters'], initial_capital, commission)
    elif strategy['Code'] == 'rsi_strategy':
        results = backtest_rsi_strategy(data, strategy['Parameters'], initial_capital, commission)
    elif strategy['Code'] == 'bollinger_bands_strategy':
        results = backtest_bollinger_strategy(data, strategy['Parameters'], initial_capital, commission)
    else:
        return {"error": f"Strategy code '{strategy['Code']}' not implemented"}
    
    # Store backtest results
    start_date = data['Date'].min() if 'Date' in data.columns else data.index.min()
    end_date = data['Date'].max() if 'Date' in data.columns else data.index.max()
    
    query = """
    INSERT INTO backtest_results 
    (StrategyID, Ticker, StartDate, EndDate, InitialCapital, FinalCapital, Returns, SharpeRatio, MaxDrawdown)
    VALUES (:strategy_id, :ticker, :start_date, :end_date, :initial_capital, :final_capital, :returns, :sharpe, :max_drawdown)
    """
    
    with engine.begin() as conn:
        conn.execute(
            text(query), 
            {
                'strategy_id': strategy_id,
                'ticker': ticker,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'final_capital': results['final_capital'],
                'returns': results['total_return'],
                'sharpe': results['sharpe_ratio'],
                'max_drawdown': results['max_drawdown']
            }
        )
    
    return results

def backtest_ma_crossover(data, parameters, initial_capital=10000, commission=0.001):
    """
    Backtest a moving average crossover strategy
    
    Args:
        data (pandas.DataFrame): Price data
        parameters (dict): Strategy parameters
        initial_capital (float): Initial capital
        commission (float): Commission rate
    
    Returns:
        dict: Backtest results
    """
    # Extract parameters
    fast_period = parameters.get('fast_period', 20)
    slow_period = parameters.get('slow_period', 50)
    
    # Ensure we have the right column names
    if 'Close' not in data.columns and 'close' in data.columns:
        data['Close'] = data['close']
    
    # Calculate moving averages
    data['fast_ma'] = data['Close'].rolling(window=fast_period).mean()
    data['slow_ma'] = data['Close'].rolling(window=slow_period).mean()
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['fast_ma'] > data['slow_ma'], 'signal'] = 1
    data.loc[data['fast_ma'] < data['slow_ma'], 'signal'] = -1
    
    # Calculate position changes
    data['position'] = data['signal'].diff()
    
    # Initialize portfolio and holdings
    data['holdings'] = 0
    data['cash'] = initial_capital
    data['portfolio'] = initial_capital
    
    # Simulate trading
    for i in range(1, len(data)):
        # If position changed
        if data['position'].iloc[i] != 0:
            # Buy signal
            if data['position'].iloc[i] > 0:
                # Calculate shares to buy
                shares = data['cash'].iloc[i-1] // (data['Close'].iloc[i] * (1 + commission))
                # Update holdings and cash
                data.loc[data.index[i], 'holdings'] = shares * data['Close'].iloc[i]
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1] - shares * data['Close'].iloc[i] * (1 + commission)
            # Sell signal
            elif data['position'].iloc[i] < 0:
                # Calculate value of holdings
                sell_value = data['holdings'].iloc[i-1] * (1 - commission)
                # Update holdings and cash
                data.loc[data.index[i], 'holdings'] = 0
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1] + sell_value
        else:
            # No change in position
            if data['signal'].iloc[i] == 1:  # Long position
                # Update holdings value
                shares = data['holdings'].iloc[i-1] / data['Close'].iloc[i-1]
                data.loc[data.index[i], 'holdings'] = shares * data['Close'].iloc[i]
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1]
            else:  # No position or short position
                data.loc[data.index[i], 'holdings'] = 0
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1]
        
        # Update portfolio value
        data.loc[data.index[i], 'portfolio'] = data['holdings'].iloc[i] + data['cash'].iloc[i]
    
    # Calculate returns
    data['returns'] = data['portfolio'].pct_change()
    
    # Calculate metrics
    total_return = (data['portfolio'].iloc[-1] / initial_capital) - 1
    annual_return = (1 + total_return) ** (252 / len(data)) - 1
    daily_returns = data['returns'].dropna()
    sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
    
    # Calculate drawdown
    data['cumulative_return'] = (1 + data['returns']).cumprod()
    data['cumulative_max'] = data['cumulative_return'].cummax()
    data['drawdown'] = (data['cumulative_return'] / data['cumulative_max']) - 1
    max_drawdown = data['drawdown'].min()
    
    # Generate equity curve plot
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['portfolio'], label='Portfolio Value')
    plt.title('Equity Curve')
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
    equity_curve = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Generate signals plot
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(data.index, data['Close'], label='Close Price')
    plt.plot(data.index, data['fast_ma'], label=f'Fast MA ({fast_period})')
    plt.plot(data.index, data['slow_ma'], label=f'Slow MA ({slow_period})')
    plt.title('Price and Moving Averages')
    plt.ylabel('Price')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(data.index, data['signal'], label='Signal')
    plt.title('Trading Signals')
    plt.xlabel('Date')
    plt.ylabel('Signal')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    signals_plot = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return {
        'initial_capital': initial_capital,
        'final_capital': float(data['portfolio'].iloc[-1]),
        'total_return': float(total_return),
        'annual_return': float(annual_return),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
        'equity_curve': f'data:image/png;base64,{equity_curve}',
        'signals_plot': f'data:image/png;base64,{signals_plot}'
    }

def backtest_rsi_strategy(data, parameters, initial_capital=10000, commission=0.001):
    """
    Backtest an RSI strategy
    
    Args:
        data (pandas.DataFrame): Price data
        parameters (dict): Strategy parameters
        initial_capital (float): Initial capital
        commission (float): Commission rate
    
    Returns:
        dict: Backtest results
    """
    # Extract parameters
    rsi_period = parameters.get('rsi_period', 14)
    overbought = parameters.get('overbought', 70)
    oversold = parameters.get('oversold', 30)
    
    # Ensure we have the right column names
    if 'Close' not in data.columns and 'close' in data.columns:
        data['Close'] = data['close']
    
    # Calculate RSI
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()
    
    rs = avg_gain / avg_loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['rsi'] < oversold, 'signal'] = 1  # Buy when RSI is oversold
    data.loc[data['rsi'] > overbought, 'signal'] = -1  # Sell when RSI is overbought
    
    # Calculate position changes
    data['position'] = data['signal'].diff()
    
    # Initialize portfolio and holdings
    data['holdings'] = 0
    data['cash'] = initial_capital
    data['portfolio'] = initial_capital
    
    # Simulate trading
    for i in range(1, len(data)):
        # If position changed
        if data['position'].iloc[i] != 0:
            # Buy signal
            if data['position'].iloc[i] > 0:
                # Calculate shares to buy
                shares = data['cash'].iloc[i-1] // (data['Close'].iloc[i] * (1 + commission))
                # Update holdings and cash
                data.loc[data.index[i], 'holdings'] = shares * data['Close'].iloc[i]
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1] - shares * data['Close'].iloc[i] * (1 + commission)
            # Sell signal
            elif data['position'].iloc[i] < 0:
                # Calculate value of holdings
                sell_value = data['holdings'].iloc[i-1] * (1 - commission)
                # Update holdings and cash
                data.loc[data.index[i], 'holdings'] = 0
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1] + sell_value
        else:
            # No change in position
            if data['signal'].iloc[i] == 1:  # Long position
                # Update holdings value
                shares = data['holdings'].iloc[i-1] / data['Close'].iloc[i-1] if data['Close'].iloc[i-1] != 0 else 0
                data.loc[data.index[i], 'holdings'] = shares * data['Close'].iloc[i]
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1]
            else:  # No position or short position
                data.loc[data.index[i], 'holdings'] = 0
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1]
        
        # Update portfolio value
        data.loc[data.index[i], 'portfolio'] = data['holdings'].iloc[i] + data['cash'].iloc[i]
    
    # Calculate returns
    data['returns'] = data['portfolio'].pct_change()
    
    # Calculate metrics
    total_return = (data['portfolio'].iloc[-1] / initial_capital) - 1
    annual_return = (1 + total_return) ** (252 / len(data)) - 1
    daily_returns = data['returns'].dropna()
    sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std() if daily_returns.std() != 0 else 0
    
    # Calculate drawdown
    data['cumulative_return'] = (1 + data['returns']).cumprod()
    data['cumulative_max'] = data['cumulative_return'].cummax()
    data['drawdown'] = (data['cumulative_return'] / data['cumulative_max']) - 1
    max_drawdown = data['drawdown'].min()
    
    # Generate equity curve plot
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['portfolio'], label='Portfolio Value')
    plt.title('Equity Curve')
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
    equity_curve = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Generate signals plot
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(data.index, data['Close'], label='Close Price')
    plt.title('Price')
    plt.ylabel('Price')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(data.index, data['rsi'], label='RSI')
    plt.axhline(y=overbought, color='r', linestyle='-', alpha=0.3)
    plt.axhline(y=oversold, color='g', linestyle='-', alpha=0.3)
    plt.title('RSI')
    plt.xlabel('Date')
    plt.ylabel('RSI')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    signals_plot = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return {
        'initial_capital': initial_capital,
        'final_capital': float(data['portfolio'].iloc[-1]),
        'total_return': float(total_return),
        'annual_return': float(annual_return),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
        'equity_curve': f'data:image/png;base64,{equity_curve}',
        'signals_plot': f'data:image/png;base64,{signals_plot}'
    }

def backtest_bollinger_strategy(data, parameters, initial_capital=10000, commission=0.001):
    """
    Backtest a Bollinger Bands strategy
    
    Args:
        data (pandas.DataFrame): Price data
        parameters (dict): Strategy parameters
        initial_capital (float): Initial capital
        commission (float): Commission rate
    
    Returns:
        dict: Backtest results
    """
    # Extract parameters
    window = parameters.get('window', 20)
    num_std = parameters.get('num_std', 2)
    
    # Ensure we have the right column names
    if 'Close' not in data.columns and 'close' in data.columns:
        data['Close'] = data['close']
    
    # Calculate Bollinger Bands
    data['ma'] = data['Close'].rolling(window=window).mean()
    data['std'] = data['Close'].rolling(window=window).std()
    data['upper'] = data['ma'] + (data['std'] * num_std)
    data['lower'] = data['ma'] - (data['std'] * num_std)
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['Close'] < data['lower'], 'signal'] = 1  # Buy when price is below lower band
    data.loc[data['Close'] > data['upper'], 'signal'] = -1  # Sell when price is above upper band
    
    # Calculate position changes
    data['position'] = data['signal'].diff()
    
    # Initialize portfolio and holdings
    data['holdings'] = 0
    data['cash'] = initial_capital
    data['portfolio'] = initial_capital
    
    # Simulate trading
    for i in range(1, len(data)):
        # If position changed
        if data['position'].iloc[i] != 0:
            # Buy signal
            if data['position'].iloc[i] > 0:
                # Calculate shares to buy
                shares = data['cash'].iloc[i-1] // (data['Close'].iloc[i] * (1 + commission))
                # Update holdings and cash
                data.loc[data.index[i], 'holdings'] = shares * data['Close'].iloc[i]
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1] - shares * data['Close'].iloc[i] * (1 + commission)
            # Sell signal
            elif data['position'].iloc[i] < 0:
                # Calculate value of holdings
                sell_value = data['holdings'].iloc[i-1] * (1 - commission)
                # Update holdings and cash
                data.loc[data.index[i], 'holdings'] = 0
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1] + sell_value
        else:
            # No change in position
            if data['signal'].iloc[i] == 1:  # Long position
                # Update holdings value
                shares = data['holdings'].iloc[i-1] / data['Close'].iloc[i-1] if data['Close'].iloc[i-1] != 0 else 0
                data.loc[data.index[i], 'holdings'] = shares * data['Close'].iloc[i]
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1]
            else:  # No position or short position
                data.loc[data.index[i], 'holdings'] = 0
                data.loc[data.index[i], 'cash'] = data['cash'].iloc[i-1]
        
        # Update portfolio value
        data.loc[data.index[i], 'portfolio'] = data['holdings'].iloc[i] + data['cash'].iloc[i]
    
    # Calculate returns
    data['returns'] = data['portfolio'].pct_change()
    
    # Calculate metrics
    total_return = (data['portfolio'].iloc[-1] / initial_capital) - 1
    annual_return = (1 + total_return) ** (252 / len(data)) - 1
    daily_returns = data['returns'].dropna()
    sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std() if daily_returns.std() != 0 else 0
    
    # Calculate drawdown
    data['cumulative_return'] = (1 + data['returns']).cumprod()
    data['cumulative_max'] = data['cumulative_return'].cummax()
    data['drawdown'] = (data['cumulative_return'] / data['cumulative_max']) - 1
    max_drawdown = data['drawdown'].min()
    
    # Generate equity curve plot
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['portfolio'], label='Portfolio Value')
    plt.title('Equity Curve')
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
    equity_curve = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Generate signals plot
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(data.index, data['Close'], label='Close Price')
    plt.plot(data.index, data['ma'], label=f'MA({window})')
    plt.plot(data.index, data['upper'], label='Upper Band')
    plt.plot(data.index, data['lower'], label='Lower Band')
    plt.fill_between(data.index, data['upper'], data['lower'], alpha=0.1)
    plt.title('Price and Bollinger Bands')
    plt.ylabel('Price')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(data.index, data['signal'], label='Signal')
    plt.title('Trading Signals')
    plt.xlabel('Date')
    plt.ylabel('Signal')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    signals_plot = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return {
        'initial_capital': initial_capital,
        'final_capital': float(data['portfolio'].iloc[-1]),
        'total_return': float(total_return),
        'annual_return': float(annual_return),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
        'equity_curve': f'data:image/png;base64,{equity_curve}',
        'signals_plot': f'data:image/png;base64,{signals_plot}'
    }

def optimize_strategy(strategy_code, ticker, parameters_range, metric='sharpe_ratio', start_date=None, end_date=None):
    """
    Optimize strategy parameters
    
    Args:
        strategy_code (str): Strategy code
        ticker (str): Ticker symbol
        parameters_range (dict): Range of parameters to test
        metric (str): Metric to optimize ('sharpe_ratio', 'total_return', 'max_drawdown')
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    
    Returns:
        dict: Optimization results
    """
    # Get ticker data
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
        data = pd.DataFrame(result.fetchall())
    
    if data.empty:
        return {"error": f"No data found for {ticker}"}
    
    # Initialize results
    results = []
    
    # Moving Average Crossover strategy optimization
    if strategy_code == 'moving_average_crossover':
        fast_periods = parameters_range.get('fast_period', range(5, 51, 5))
        slow_periods = parameters_range.get('slow_period', range(20, 201, 20))
        
        for fast_period in fast_periods:
            for slow_period in slow_periods:
                if fast_period >= slow_period:
                    continue
                
                parameters = {'fast_period': fast_period, 'slow_period': slow_period}
                backtest_result = backtest_ma_crossover(data, parameters)
                
                results.append({
                    'parameters': parameters,
                    'sharpe_ratio': backtest_result['sharpe_ratio'],
                    'total_return': backtest_result['total_return'],
                    'max_drawdown': backtest_result['max_drawdown']
                })
    
    elif strategy_code == 'rsi_strategy':
        rsi_periods = parameters_range.get('rsi_period', range(5, 31, 5))
        overbought_levels = parameters_range.get('overbought', range(60, 91, 5))
        oversold_levels = parameters_range.get('oversold', range(10, 41, 5))
        
        for rsi_period in rsi_periods:
            for overbought in overbought_levels:
                for oversold in oversold_levels:
                    if oversold >= overbought:
                        continue
                    parameters = {
                        'rsi_period': rsi_period,
                        'overbought': overbought,
                        'oversold': oversold
                    }
                    backtest_result = backtest_rsi_strategy(data, parameters)
                    results.append({
                        'parameters': parameters,
                        'sharpe_ratio': backtest_result['sharpe_ratio'],
                        'total_return': backtest_result['total_return'],
                        'max_drawdown': backtest_result['max_drawdown']
                    })
                    
    # Bollinger Bands strategy optimization
    elif strategy_code == 'bollinger_bands_strategy':
        windows = parameters_range.get('window', range(10, 51, 10))
        num_stds = parameters_range.get('num_std', [1.5, 2.0, 2.5, 3.0])
        
        for window in windows:
            for num_std in num_stds:
                parameters = {'window': window, 'num_std': num_std}
                backtest_result = backtest_bollinger_strategy(data, parameters)
                
                results.append({
                    'parameters': parameters,
                    'sharpe_ratio': backtest_result['sharpe_ratio'],
                    'total_return': backtest_result['total_return'],
                    'max_drawdown': backtest_result['max_drawdown']
                })
    
    else:
        return {"error": f"Strategy code '{strategy_code}' not implemented for optimization"}
    
    # Sort results by the specified metric
    if metric == 'sharpe_ratio':
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
    elif metric == 'total_return':
        results.sort(key=lambda x: x['total_return'], reverse=True)
    elif metric == 'max_drawdown':
        results.sort(key=lambda x: x['max_drawdown'])
    
    # Get the best parameters
    best_result = results[0]
    
    # Create a new strategy with the optimized parameters
    strategy_name = f"Optimized {strategy_code.replace('_', ' ').title()}"
    strategy_description = f"Optimized {strategy_code} strategy for {ticker}"
    
    strategy_id = create_strategy(strategy_name, f"{strategy_code}_optimized", strategy_description, best_result['parameters'])
    
    return {
        'strategy_id': strategy_id,
        'best_parameters': best_result['parameters'],
        'best_sharpe_ratio': best_result['sharpe_ratio'],
        'best_total_return': best_result['total_return'],
        'best_max_drawdown': best_result['max_drawdown'],
        'all_results': results[:10]  # Return top 10 results
    }
