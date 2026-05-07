"""Compatibility shim for legacy import path.

Historically, FinanceTools lived under my_toolbox.finance_tools.
The implementation now lives in finance_toolbox.finance_tools.
This module preserves backward compatibility for existing callers/tests.
"""

from finance_toolbox.finance_tools import FinanceTools, HAS_YFINANCE, yf, time

__all__ = ["FinanceTools", "HAS_YFINANCE", "yf", "time"]
