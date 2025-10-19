# Samsung Phone Advisor & AlgoTrader: Core Documentation

This repository contains two distinct projects: **Samsung Phone Advisor** and **AlgoTrader**. Each project has its own dedicated README file for detailed setup and usage instructions. This core README provides an overview of both tasks and links to their respective documentation.

## Projects Overview

### 1. AlgoTrader
A Python-based algorithmic trading system that implements the Golden Cross strategy using moving averages (50-day and 200-day) to trade stocks. It downloads historical stock data, processes it, and simulates trading with a given budget.

- **Key Features**:
  - Downloads historical stock data using `yfinance`.
  - Cleans data and calculates moving averages.
  - Executes buy/sell decisions based on Golden Cross (buy) and Death Cross (sell) signals.
  - Tracks and reports trading performance (profit/loss, ROI).
- **Tech Stack**: Python, yfinance, pandas.
- **Detailed Documentation**: See [README.md](https://github.com/nahidn4p/GTRBD-SUBMISSION/blob/main/Algo-Trader/readme.md) for setup and usage instructions.

### 2. Samsung Phone Advisor
A FastAPI-based application that scrapes Samsung phone specifications from GSMArena, stores them in a PostgreSQL database, and provides an API to answer user queries about phone comparisons or specifications. It supports natural-language queries like "Compare Samsung Galaxy M36 and F56" or "Best battery under $1000".

- **Key Features**:
  - Web scraping of Samsung phone specs using BeautifulSoup and Requests.
  - Stores data in a PostgreSQL database with SQLAlchemy.
  - Handles comparison queries and filtered searches via a FastAPI endpoint.
  - Uses regex for robust parsing of phone models and specifications.
- **Tech Stack**: Python, FastAPI, PostgreSQL, BeautifulSoup, Requests.
- **Detailed Documentation**: See [README.md](https://github.com/nahidn4p/GTRBD-SUBMISSION/blob/main/Samsung-Phone-Advisor/readme.md) for setup, usage, and troubleshooting instructions.



## Getting Started
Each project is independent and can be set up separately. Refer to the individual README files for specific installation steps, prerequisites, and usage examples:
- For **Samsung Phone Advisor**, follow the instructions in [README.md](https://github.com/nahidn4p/GTRBD-SUBMISSION/blob/main/Samsung-Phone-Advisor/readme.md).
- For **AlgoTrader**, follow the instructions in [README.md]([AlgoTrader_README.md](https://github.com/nahidn4p/GTRBD-SUBMISSION/blob/main/Algo-Trader/readme.md)).

## Repository Structure
```
├── README.md                # Samsung Phone Advisor README
├── AlgoTrader_README.md     # AlgoTrader README
├── CORE_README.md           # This core documentation
├── samsung_phone_advisor/   # Samsung Phone Advisor source code
│   ├── app.py
│   ├── requirements.txt
│   └── readme.md
├── algo_trader/             # AlgoTrader source code
│   ├── algo_trader.py
│   ├── requirements.txt
|   |── models.py
│   └── readme.md
```
