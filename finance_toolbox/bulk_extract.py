import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from my_toolbox.yfinance_tools import YFTools  # Assumes the code above is in yfinance_tools.py

# Setup basic logging to see progress
logging.basicConfig(level=logging.INFO)

def process_stock(symbol):
    """Worker: Init tool, pull everything, dump to JSON."""
    try:
        tool = YFTools(symbol)
        output_file = tool.export_full_snapshot_json()
        return f"SUCCESS: {symbol} saved to {output_file}"
    except Exception as e:
        return f"ERROR: {symbol} failed with: {str(e)}"

if __name__ == "__main__":
    # Add your list of tickers here
    portfolio = ["WMT"]
    
    print(f"Starting extraction for {len(portfolio)} stocks...")

    # max_workers=3 is the "sweet spot" to avoid getting banned
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_stock, ticker): ticker for ticker in portfolio}
        
        for future in as_completed(futures):
            print(future.result())

    print("\nAll tasks complete. You can now use the JSON files for charting.")