import pandas as pd

def moving_average(data, window):
    return data['close'].rolling(window=window).mean()

def backtest_strategy(data):
    # Implementa tu lógica de backtesting aquí
    pass 