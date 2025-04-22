from fastapi import FastAPI, HTTPException, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import yfinance as yf
import pandas as pd
import json
from typing import List, Optional
from datetime import datetime, timedelta

from app.DB.DataBase import get_db_connection, initialize_database
from app.data_fetcher import fetch_ticker_data, get_available_tickers, get_ticker_data_from_db
from app.analysis import analyze_ticker, analyze_correlation
from app.indicators import plot_indicator
from app.backtest import create_strategy, get_strategy, get_all_strategies, run_backtest, optimize_strategy

# Create directories if they don't exist
os.makedirs('data/graficos', exist_ok=True)
os.makedirs('data/reportes', exist_ok=True)
os.makedirs('app/static', exist_ok=True)
os.makedirs('app/templates', exist_ok=True)

# Initialize the database
initialize_database()

# Create FastAPI app
app = FastAPI(title="Financial Data Analysis Application")

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the home page"""
    # Get available tickers
    tickers = get_available_tickers()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tickers": tickers
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard page"""
    # Get available tickers
    tickers = get_available_tickers()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "tickers": tickers
    })

@app.get("/data", response_class=HTMLResponse)
async def data_page(request: Request):
    """Render the data management page"""
    # Get available tickers
    tickers = get_available_tickers()
    
    return templates.TemplateResponse("data.html", {
        "request": request,
        "tickers": tickers
    })

@app.post("/fetch-data")
async def fetch_data(ticker: str = Form(...), period: str = Form("1y"), interval: str = Form("1d")):
    """Fetch data for a ticker"""
    try:
        data = fetch_ticker_data(ticker, period, interval)
        if data is None:
            return {"success": False, "message": f"Failed to fetch data for {ticker}"}
        
        return {"success": True, "message": f"Successfully fetched data for {ticker}", "rows": len(data)}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """Render the analysis page"""
    # Get available tickers
    tickers = get_available_tickers()
    
    return templates.TemplateResponse("analysis.html", {
        "request": request,
        "tickers": tickers
    })

@app.post("/analyze-ticker")
async def analyze_ticker_endpoint(ticker: str = Form(...), period: str = Form("1y")):
    """Analyze a ticker"""
    try:
        # Convert period to dates
        end_date = datetime.now().date()
        if period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        elif period == "5y":
            start_date = end_date - timedelta(days=1825)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        # Get data from database
        data = get_ticker_data_from_db(ticker, start_date.isoformat(), end_date.isoformat())
        
        if data is None or data.empty:
            # Fetch data if not in database
            data = fetch_ticker_data(ticker, period)
            if data is None:
                return {"success": False, "message": f"No data found for {ticker}"}
        
        # Analyze ticker
        analysis_result = analyze_ticker(ticker, data)
        
        return {"success": True, "analysis": analysis_result}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/analyze-correlation")
async def analyze_correlation_endpoint(tickers: str = Form(...), period: str = Form("1y")):
    """Analyze correlation between tickers"""
    try:
        # Parse tickers
        ticker_list = [t.strip() for t in tickers.split(',')]
        
        # Analyze correlation
        correlation_result = analyze_correlation(ticker_list, period)
        
        if "error" in correlation_result:
            return {"success": False, "message": correlation_result["error"]}
        
        return {"success": True, "correlation": correlation_result}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/indicators", response_class=HTMLResponse)
async def indicators_page(request: Request):
    """Render the indicators page"""
    # Get available tickers
    tickers = get_available_tickers()
    
    return templates.TemplateResponse("indicators.html", {
        "request": request,
        "tickers": tickers
    })

@app.post("/plot-indicator")
async def plot_indicator_endpoint(
    ticker: str = Form(...),
    indicator: str = Form(...),
    period: str = Form("1y"),
    window: int = Form(20),
    fast_period: int = Form(12),
    slow_period: int = Form(26),
    signal_period: int = Form(9),
    num_std: float = Form(2.0)
):
    """Plot an indicator for a ticker"""
    try:
        # Get data from database
        end_date = datetime.now().date()
        if period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        elif period == "5y":
            start_date = end_date - timedelta(days=1825)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        # Get data from database
        data = get_ticker_data_from_db(ticker, start_date.isoformat(), end_date.isoformat())
        
        if data is None or data.empty:
            # Fetch data if not in database
            data = fetch_ticker_data(ticker, period)
            if data is None:
                return {"success": False, "message": f"No data found for {ticker}"}
        
        # Plot indicator
        if indicator == "moving_average":
            plot = plot_indicator(data, indicator, window=window)
        elif indicator == "ema":
            plot = plot_indicator(data, indicator, window=window)
        elif indicator == "rsi":
            plot = plot_indicator(data, indicator, window=window)
        elif indicator == "bollinger":
            plot = plot_indicator(data, indicator, window=window, num_std=num_std)
        elif indicator == "macd":
            plot = plot_indicator(data, indicator, fast=fast_period, slow=slow_period, signal=signal_period)
        else:
            return {"success": False, "message": f"Indicator '{indicator}' not implemented"}
        
        return {"success": True, "plot": plot}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/strategies", response_class=HTMLResponse)
async def strategies_page(request: Request):
    """Render the strategies page"""
    # Get available tickers
    tickers = get_available_tickers()
    
    # Get all strategies
    strategies = get_all_strategies()
    
    return templates.TemplateResponse("strategies.html", {
        "request": request,
        "tickers": tickers,
        "strategies": strategies
    })

@app.post("/create-strategy")
async def create_strategy_endpoint(
    name: str = Form(...),
    code: str = Form(...),
    description: str = Form(...),
    parameters: str = Form(...)
):
    """Create a new strategy"""
    try:
        # Parse parameters
        params = json.loads(parameters)
        
        # Create strategy
        strategy_id = create_strategy(name, code, description, params)
        
        return {"success": True, "strategy_id": strategy_id}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/run-backtest")
async def run_backtest_endpoint(
    strategy_id: int = Form(...),
    ticker: str = Form(...),
    period: str = Form("1y"),
    initial_capital: float = Form(10000),
    commission: float = Form(0.001)
):
    """Run a backtest for a strategy"""
    try:
        # Convert period to dates
        end_date = datetime.now().date()
        if period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        elif period == "5y":
            start_date = end_date - timedelta(days=1825)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        # Run backtest
        backtest_result = run_backtest(
            strategy_id, 
            ticker, 
            start_date.isoformat(), 
            end_date.isoformat(), 
            initial_capital, 
            commission
        )
        
        if "error" in backtest_result:
            return {"success": False, "message": backtest_result["error"]}
        
        return {"success": True, "backtest": backtest_result}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/optimize-strategy")
async def optimize_strategy_endpoint(
    strategy_code: str = Form(...),
    ticker: str = Form(...),
    period: str = Form("1y"),
    metric: str = Form("sharpe_ratio"),
    parameters_range: str = Form(...)
):
    """Optimize strategy parameters"""
    try:
        # Parse parameters range
        params_range = json.loads(parameters_range)
        
        # Convert period to dates
        end_date = datetime.now().date()
        if period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        elif period == "5y":
            start_date = end_date - timedelta(days=1825)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        # Optimize strategy
        optimization_result = optimize_strategy(
            strategy_code,
            ticker,
            params_range,
            metric,
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        if "error" in optimization_result:
            return {"success": False, "message": optimization_result["error"]}
        
        return {"success": True, "optimization": optimization_result}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Render the reports page"""
    # Get available tickers
    tickers = get_available_tickers()
    
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "tickers": tickers
    })

@app.post("/generate-report")
async def generate_report_endpoint(ticker: str = Form(...), period: str = Form("1y")):
    """Generate a comprehensive report for a ticker"""
    try:
        # Convert period to dates
        end_date = datetime.now().date()
        if period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        elif period == "5y":
            start_date = end_date - timedelta(days=1825)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        # Get data from database
        data = get_ticker_data_from_db(ticker, start_date.isoformat(), end_date.isoformat())
        
        if data is None or data.empty:
            # Fetch data if not in database
            data = fetch_ticker_data(ticker, period)
            if data is None:
                return {"success": False, "message": f"No data found for {ticker}"}
        
        # Analyze ticker
        analysis_result = analyze_ticker(ticker, data)
        
        # Get all strategies
        strategies = get_all_strategies()
        
        # Run backtests for all strategies
        backtest_results = []
        for strategy in strategies:
            try:
                backtest_result = run_backtest(
                    strategy['ID'],
                    ticker,
                    start_date.isoformat(),
                    end_date.isoformat()
                )
                backtest_results.append({
                    'strategy': strategy,
                    'result': backtest_result
                })
            except Exception as e:
                print(f"Error running backtest for strategy {strategy['ID']}: {e}")
        
        # Generate report
        report = {
            'ticker': ticker,
            'period': period,
            'analysis': analysis_result,
            'backtest_results': backtest_results
        }
        
        # Save report to file
        report_file = f"data/reportes/{ticker}_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return {"success": True, "report": report, "file": report_file}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
