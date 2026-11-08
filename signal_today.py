"""Print the portfolio to hold from the next session (decided on the latest close).

Run after the US close: python signal_today.py
"""
from __future__ import annotations

import json

from strategy.books import target_portfolio

if __name__ == "__main__":
    print(json.dumps(target_portfolio(), indent=2))
