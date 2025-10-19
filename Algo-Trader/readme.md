# AlgoTrader: Golden Cross Strategy

## Overview
This project implements a simple algorithmic trading strategy based on the Golden Cross and Death Cross signals using Python. The strategy uses 50-day and 200-day moving averages to make buy and sell decisions for a specified stock. The code downloads historical stock data, processes it, and simulates trading with a given budget.

## Features
- Downloads historical stock data using `yfinance`.
- Cleans data by removing duplicates and handling missing values.
- Calculates 50-day and 200-day moving averages.
- Implements the Golden Cross strategy:
  - **Buy**: When the 50-day MA crosses above the 200-day MA.
  - **Sell**: When the 50-day MA crosses below the 200-day MA.
- Tracks trading performance, including profit/loss and ROI.
- Supports customizable stock symbols, date ranges, and initial budget.

## System Architecture

```mermaid
graph TD
    A[Start] --> B[Initialize AlgoTrader<br>symbol, from_date, to_date, budget]
    B --> C[download_data]<br>Fetch stock data from yfinance
    C --> D[clean_data]<br>Remove duplicates, forward-fill NaNs
    D --> E[calculate_moving_averages]<br>Compute MA50, MA200
    E --> F[apply_strategy]<br>Loop through data
    F -->|For each day| G{MA50 crosses MA200?}
    G -->|MA50 > MA200<br>Golden Cross| H{No position?}
    H -->|Yes| I[buy_stock]<br>Buy shares with available cash
    G -->|MA50 < MA200<br>Death Cross| J{Holding position?}
    J -->|Yes| K[sell_stock]<br>Sell shares, update profit
    I --> L[Next Day]
    K --> L
    J -->|No| L
    H -->|No| L
    L -->|End of data| M{Holding position?}
    M -->|Yes| N[sell_stock]<br>Force close position
    N --> O[evaluate_performance]<br>Print final report
    M -->|No| O
    O --> P[End]
```

## Requirements
- Python 3.6+
- Required libraries:
  - `yfinance`: For downloading stock data.
  - `pandas`: For data manipulation.
- Install dependencies using:
  ```bash
  pip install yfinance pandas
  ```

## Usage
1. **Clone the repository** or save the script as `algo_trader.py`.
2. **Run the script** with default parameters:
   ```bash
   python algo_trader.py
   ```
   This runs the strategy for Apple (AAPL) from 2018-01-01 to 2023-12-31 with a default budget of $5000.
3. **Customize parameters** by modifying the `AlgoTrader` initialization:
   ```python
   trader = AlgoTrader(symbol="MSFT", from_date="2020-01-01", to_date="2025-12-31", budget=10000)
   trader.download_data()
   trader.clean_data()
   trader.calculate_moving_averages()
   trader.apply_strategy()
   trader.evaluate_performance()
   ```

## Code Structure
- **Class**: `AlgoTrader`
  - `__init__`: Initializes the trader with stock symbol, date range, and budget.
  - `get_scalar`: Utility method to safely convert pandas data to float.
  - `download_data`: Downloads historical stock data using `yfinance`.
  - `clean_data`: Removes duplicate indices and forward-fills missing values.
  - `calculate_moving_averages`: Computes 50-day and 200-day moving averages.
  - `apply_strategy`: Executes the Golden Cross/Death Cross trading logic.
  - `buy_stock`/`sell_stock`: Handles buying and selling shares.
  - `evaluate_performance`: Reports final trading performance metrics.

## Example Output
```
Downloading AAPL data from 2018-01-01 to 2023-12-31...
Data downloaded successfully!
Cleaning data...
Data cleaned successfully!
Moving averages calculated!
Applying Golden Cross strategy...
Bought 115 shares of AAPL at $43.06
Sold 115 shares of AAPL at $130.96 | Trade Profit: $10108.50
Position forcefully closed at the end of data period.

========== FINAL REPORT ==========
Symbol: AAPL
Initial Budget: $5000.00
Ending Cash: $15054.50
Total Profit/Loss: $10108.50
Return on Investment: 201.17%
==================================
```

## Limitations
- The strategy is simplistic and does not account for trading fees, slippage, or taxes.
- It assumes sufficient liquidity for all trades.
- Historical data is subject to `yfinance` API availability and accuracy.
- The strategy only holds one position at a time and force-closes positions at the end of the data period.

