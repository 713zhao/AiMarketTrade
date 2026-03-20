#!/usr/bin/env python
"""
Simple Flask startup script for the trading dashboard.
Run with: .venv\Scripts\python.exe run_dashboard.py
"""

import sys
import os

# Make sure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

print("=" * 60)
print("Trading System Dashboard Launcher")
print("=" * 60)

# Import and run the dashboard
try:
    import web_dashboard_trading
    # The dashboard app runs when this module is executed
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
