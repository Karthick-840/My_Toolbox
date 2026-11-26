from my_toolbox.yfinance_tools import YFTools
import pandas as pd

# Initialize the tool
yf_tool = YFTools("WMT")
ticker = "WMT"

# ==========================================
# TEST 1: Metadata & Profile (The Leaf)
# ==========================================
# print("--- Testing Metadata & Profile ---")
# profile = yf_tool.get_full_profile()
# print(f"Symbol: {profile['symbol']}")
# print(f"Sector: {profile['sector']}")
# print(f"Summary: {profile['summary'][:100]}...")


# ==========================================
# TEST 2: Financial Statements (The Composite)
# ==========================================
# print("\n--- Testing Annual Financials ---")
# financials = yf_tool.get_financial_statements(quarterly=False)
# print("Income Statement (Last 2 years):")
# print(financials['income_stmt'].iloc[:, :2])

# print("\n--- Testing Quarterly Balance Sheet ---")
# q_financials = yf_tool.get_financial_statements(quarterly=True)
# print(q_financials['balance_sheet'].iloc[:, :2])


# ==========================================
# TEST 3: Dividends & Splits (Historical Actions)
# ==========================================
# print("\n--- Testing Dividends & Splits (Filtered) ---")
# # Testing the internal date filter logic
# actions = yf_tool.get_dividends_and_splits(start_date="2021-01-01", end_date="2025-12-31")
# print(actions)


# ==========================================
# TEST 4: Analysis & Price Targets (Estimates)
# ==========================================
# print("\n--- Testing Analyst Estimates ---")
# analysis = yf_tool.get_analysis_estimates()
# print("Price Targets:")
# print(analysis['price_targets'])
# print("\nRevenue Estimates:")
# print(analysis['revenue_estimate'].iloc[:, :2])


# ==========================================
# TEST 5: Ownership Data (Holders)
# ==========================================
# print("\n--- Testing Ownership Data ---")
# ownership = yf_tool.get_ownership_data()
# print("Major Holders:")
# print(ownership['major_holders'])
# print("\nInstitutional Holders (Top 5):")
# print(ownership['institutional_holders'])


# ==========================================
# TEST 6: Price History (Max with Filter)
# ==========================================
# print("\n--- Testing Price History ---")
# # Fetches 'max' history then applies local filtering for speed and control
# history = yf_tool.get_price_history(start_date="2020-01-01")
# print(f"History rows retrieved: {len(history)}")
# print(history.tail())