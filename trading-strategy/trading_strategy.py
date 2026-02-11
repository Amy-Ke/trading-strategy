"""
Simple Moving Average Crossover Trading Strategy
Author: Amy Ke
Description: Backtests a trading strategy using 50-day and 200-day moving averages
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class MovingAverageCrossover:
    def __init__(self, ticker='SPY', start_date=None, end_date=None, 
                 short_window=50, long_window=200, initial_capital=100000):
        """
        Initialize the trading strategy
        
        Parameters:
        - ticker: Stock symbol (default: SPY - S&P 500 ETF)
        - start_date: Start date for backtest (default: 5 years ago)
        - end_date: End date for backtest (default: today)
        - short_window: Short moving average period (default: 50 days)
        - long_window: Long moving average period (default: 200 days)
        - initial_capital: Starting portfolio value (default: $100,000)
        """
        self.ticker = ticker
        self.short_window = short_window
        self.long_window = long_window
        self.initial_capital = initial_capital
        
        # Set default dates if not provided
        if end_date is None:
            self.end_date = datetime.now()
        else:
            self.end_date = end_date
            
        if start_date is None:
            self.start_date = self.end_date - timedelta(days=365*5)  # 5 years
        else:
            self.start_date = start_date
    
    def download_data(self):
        """Download historical price data from Yahoo Finance"""
        print(f"Downloading {self.ticker} data from {self.start_date.date()} to {self.end_date.date()}...")
        self.data = yf.download(self.ticker, start=self.start_date, end=self.end_date)
        print(f"Downloaded {len(self.data)} days of data")
        return self.data
    
    def calculate_signals(self):
        """Calculate moving averages and generate trading signals"""
        # Calculate moving averages
        self.data['SMA_short'] = self.data['Close'].rolling(window=self.short_window).mean()
        self.data['SMA_long'] = self.data['Close'].rolling(window=self.long_window).mean()
        
        # Generate signals: 1 = buy, -1 = sell, 0 = hold
        self.data['Signal'] = 0
        self.data.loc[self.data['SMA_short'] > self.data['SMA_long'], 'Signal'] = 1
        self.data.loc[self.data['SMA_short'] < self.data['SMA_long'], 'Signal'] = -1
        
        # Identify when position changes (crossovers)
        self.data['Position'] = self.data['Signal'].diff()
        
        return self.data
    
    def backtest(self):
        """Backtest the strategy and calculate returns"""
        # Calculate daily returns
        self.data['Daily_Return'] = self.data['Close'].pct_change()
        
        # Calculate strategy returns (only earn returns when signal = 1)
        self.data['Strategy_Return'] = self.data['Daily_Return'] * self.data['Signal'].shift(1)
        
        # Calculate cumulative returns
        self.data['Buy_Hold_Return'] = (1 + self.data['Daily_Return']).cumprod()
        self.data['Strategy_Cumulative'] = (1 + self.data['Strategy_Return']).cumprod()
        
        # Calculate portfolio values
        self.data['Buy_Hold_Value'] = self.initial_capital * self.data['Buy_Hold_Return']
        self.data['Strategy_Value'] = self.initial_capital * self.data['Strategy_Cumulative']
        
        return self.data
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        # Total returns
        buy_hold_total = ((self.data['Buy_Hold_Value'].iloc[-1] / self.initial_capital) - 1) * 100
        strategy_total = ((self.data['Strategy_Value'].iloc[-1] / self.initial_capital) - 1) * 100
        
        # Annualized returns
        years = (self.end_date - self.start_date).days / 365.25
        buy_hold_annual = ((self.data['Buy_Hold_Value'].iloc[-1] / self.initial_capital) ** (1/years) - 1) * 100
        strategy_annual = ((self.data['Strategy_Value'].iloc[-1] / self.initial_capital) ** (1/years) - 1) * 100
        
        # Sharpe Ratio (assuming 0% risk-free rate for simplicity)
        strategy_sharpe = (self.data['Strategy_Return'].mean() / self.data['Strategy_Return'].std()) * np.sqrt(252)
        buyhold_sharpe = (self.data['Daily_Return'].mean() / self.data['Daily_Return'].std()) * np.sqrt(252)
        
        # Maximum Drawdown
        strategy_cummax = self.data['Strategy_Value'].cummax()
        strategy_drawdown = ((self.data['Strategy_Value'] - strategy_cummax) / strategy_cummax) * 100
        max_drawdown = strategy_drawdown.min()
        
        # Number of trades
        num_trades = (self.data['Position'] != 0).sum()
        
        metrics = {
            'Buy & Hold Total Return (%)': round(buy_hold_total, 2),
            'Strategy Total Return (%)': round(strategy_total, 2),
            'Buy & Hold Annual Return (%)': round(buy_hold_annual, 2),
            'Strategy Annual Return (%)': round(strategy_annual, 2),
            'Buy & Hold Sharpe Ratio': round(buyhold_sharpe, 2),
            'Strategy Sharpe Ratio': round(strategy_sharpe, 2),
            'Maximum Drawdown (%)': round(max_drawdown, 2),
            'Number of Trades': num_trades,
            'Initial Capital': f'${self.initial_capital:,.0f}',
            'Final Strategy Value': f'${self.data["Strategy_Value"].iloc[-1]:,.0f}',
            'Final Buy & Hold Value': f'${self.data["Buy_Hold_Value"].iloc[-1]:,.0f}'
        }
        
        return metrics
    
    def plot_results(self):
        """Create visualization of the strategy performance"""
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
        
        # Plot 1: Price and Moving Averages
        ax1.plot(self.data.index, self.data['Close'], label='Close Price', linewidth=1, alpha=0.7)
        ax1.plot(self.data.index, self.data['SMA_short'], label=f'{self.short_window}-day SMA', linewidth=1)
        ax1.plot(self.data.index, self.data['SMA_long'], label=f'{self.long_window}-day SMA', linewidth=1)
        
        # Mark buy/sell signals
        buy_signals = self.data[self.data['Position'] == 2]
        sell_signals = self.data[self.data['Position'] == -2]
        ax1.scatter(buy_signals.index, buy_signals['Close'], color='green', marker='^', s=100, label='Buy Signal', zorder=5)
        ax1.scatter(sell_signals.index, sell_signals['Close'], color='red', marker='v', s=100, label='Sell Signal', zorder=5)
        
        ax1.set_title(f'{self.ticker} - Moving Average Crossover Strategy', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Portfolio Value Over Time
        ax2.plot(self.data.index, self.data['Strategy_Value'], label='Strategy', linewidth=2, color='blue')
        ax2.plot(self.data.index, self.data['Buy_Hold_Value'], label='Buy & Hold', linewidth=2, color='orange', alpha=0.7)
        ax2.set_ylabel('Portfolio Value ($)', fontsize=11)
        ax2.set_title('Portfolio Value Over Time', fontsize=12, fontweight='bold')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Drawdown
        strategy_cummax = self.data['Strategy_Value'].cummax()
        strategy_drawdown = ((self.data['Strategy_Value'] - strategy_cummax) / strategy_cummax) * 100
        ax3.fill_between(self.data.index, strategy_drawdown, 0, color='red', alpha=0.3)
        ax3.set_ylabel('Drawdown (%)', fontsize=11)
        ax3.set_xlabel('Date', fontsize=11)
        ax3.set_title('Strategy Drawdown', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('strategy_performance.png', dpi=300, bbox_inches='tight')
        print("\nChart saved as 'strategy_performance.png'")
        plt.show()
    
    def run(self):
        """Run the complete backtest"""
        print(f"\n{'='*60}")
        print(f"MOVING AVERAGE CROSSOVER BACKTEST")
        print(f"{'='*60}")
        print(f"Ticker: {self.ticker}")
        print(f"Short MA: {self.short_window} days | Long MA: {self.long_window} days")
        print(f"Initial Capital: ${self.initial_capital:,.0f}")
        print(f"{'='*60}\n")
        
        self.download_data()
        self.calculate_signals()
        self.backtest()
        metrics = self.calculate_metrics()
        
        print("\n" + "="*60)
        print("PERFORMANCE METRICS")
        print("="*60)
        for key, value in metrics.items():
            print(f"{key:.<45} {value}")
        print("="*60 + "\n")
        
        self.plot_results()
        
        return metrics


# Example usage
if __name__ == "__main__":
    # Create and run the strategy
    strategy = MovingAverageCrossover(
        ticker='SPY',           # S&P 500 ETF
        short_window=50,        # 50-day moving average
        long_window=200,        # 200-day moving average
        initial_capital=100000  # $100,000 starting capital
    )
    
    results = strategy.run()