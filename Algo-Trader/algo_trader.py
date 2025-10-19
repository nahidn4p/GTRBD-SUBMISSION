import yfinance as yf
import pandas as pd


class AlgoTrader:
    def __init__(self, symbol: str, from_date: str, to_date: str, budget: float = 5000):
        self.symbol = symbol
        self.from_date = from_date
        self.to_date = to_date
        self.budget = budget
        self.data = None
        self.position = 0     # 0 = no position, 1 = holding stock
        self.buy_price = 0.0
        self.shares = 0
        self.cash = budget
        self.profit = 0.0

    # ------------------------------
    # Utility: safe scalar extraction
    # ------------------------------
    def get_scalar(self, value):
        """Ensure any pandas object is safely converted to a float scalar."""
        if isinstance(value, pd.Series):
            return float(value.iloc[0])
        return float(value)

    # Step 1: Download data
    def download_data(self):
        print(f"Downloading {self.symbol} data from {self.from_date} to {self.to_date}...")
        self.data = yf.download(self.symbol, start=self.from_date, end=self.to_date, auto_adjust=False) # Download daily historical stock prices
        print("Data downloaded successfully!")

    # Step 2: Clean data
    def clean_data(self):
        print("Cleaning data...")
        # Download daily historical stock prices
        self.data = self.data[~self.data.index.duplicated(keep='first')]
        # Forward-fill missing (NaN) values using previous day's data
        self.data = self.data.ffill()
        print("Data cleaned successfully!")

    # Step 3: Calculate moving averages
    def calculate_moving_averages(self):
        # Add two new columns for moving averages
        self.data["MA50"] = self.data["Close"].rolling(window=50).mean()
        self.data["MA200"] = self.data["Close"].rolling(window=200).mean()
        print("Moving averages calculated!")

    # Step 4: Apply strategy
    def apply_strategy(self):
        print("Applying Golden Cross strategy...")
        # Loop through data starting from day 1 (since we compare with previous day)
        for i in range(1, len(self.data)):
            ma50_yesterday = self.get_scalar(self.data["MA50"].iloc[i - 1])
            ma200_yesterday = self.get_scalar(self.data["MA200"].iloc[i - 1])
            ma50_today = self.get_scalar(self.data["MA50"].iloc[i])
            ma200_today = self.get_scalar(self.data["MA200"].iloc[i])
            close_price = self.get_scalar(self.data["Close"].iloc[i])

            # When 50-day MA crosses ABOVE 200-day MA send Golden Cross (Buy) signal
            if ma50_yesterday < ma200_yesterday and ma50_today > ma200_today:
                if self.position == 0:
                    self.buy_stock(close_price, self.cash)

            # when 50-day MA crosses Below 200-day MA send Death Cross (Sell) signal
            elif ma50_yesterday > ma200_yesterday and ma50_today < ma200_today:
                if self.position == 1:
                    self.sell_stock(close_price)

        # Force close open position at end
        if self.position == 1:
            last_close = self.get_scalar(self.data["Close"].iloc[-1])
            self.sell_stock(last_close)
            print("Position forcefully closed at the end of data period.")

    # Step 5: Buy and Sell methods
    def buy_stock(self, price, available_cash):
        price = self.get_scalar(price)
        #determine how many share can be brought
        self.shares = int(available_cash // price)
        if self.shares > 0:
            self.buy_price = price
            self.cash -= self.shares * price
            self.position = 1
            print(f"Bought {self.shares} shares of {self.symbol} at ${price:.2f}")

    def sell_stock(self, price):
        price = self.get_scalar(price)
        if self.position == 1:
            sell_value = self.shares * price
            self.cash += sell_value
            trade_profit = sell_value - (self.shares * self.buy_price)
            self.profit += trade_profit
            print(f"Sold {self.shares} shares of {self.symbol} at ${price:.2f} | Trade Profit: ${trade_profit:.2f}")
            self.position = 0
            self.shares = 0

    # Step 6: Evaluate performance
    def evaluate_performance(self):
        total_value = self.cash
        print("\n========== FINAL REPORT ==========")
        print(f"Symbol: {self.symbol}")
        print(f"Initial Budget: ${self.budget:.2f}")
        print(f"Ending Cash: ${self.cash:.2f}")
        print(f"Total Profit/Loss: ${self.profit:.2f}")
        print(f"Return on Investment: {((total_value - self.budget) / self.budget) * 100:.2f}%")
        print("==================================")
        return {
            "Symbol": self.symbol,
            "Initial Budget": self.budget,
            "Ending Cash": self.cash,
            "Profit/Loss": self.profit,
        }


# ------------------------------
# Output
# ------------------------------
if __name__ == "__main__":
    trader = AlgoTrader("AAPL", "2018-01-01", "2023-12-31")
    trader.download_data()
    trader.clean_data()
    trader.calculate_moving_averages()
    trader.apply_strategy()
    trader.evaluate_performance()
