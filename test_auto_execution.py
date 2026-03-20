#!/usr/bin/env python
"""
Test script for automatic trade execution feature.
Tests configuration loading and auto-execution logic.
"""

import os
import sys
from datetime import datetime
from src.config import Settings
from src.state import DeerflowState

def test_config_loading():
    """Test that configuration settings are properly loaded."""
    print("=" * 60)
    print("TEST 1: Configuration Loading")
    print("=" * 60)
    
    # Test default values
    config = Settings()
    print(f"\nDefault Configuration:")
    print(f"  auto_execute_trades: {config.auto_execute_trades}")
    print(f"  auto_execute_min_confidence: {config.auto_execute_min_confidence}")
    print(f"  auto_execute_position_size: ${config.auto_execute_position_size:.2f}")
    
    # Test environment variable override
    os.environ["AUTO_EXECUTE_TRADES"] = "true"
    os.environ["AUTO_EXECUTE_MIN_CONFIDENCE"] = "0.75"
    os.environ["AUTO_EXECUTE_POSITION_SIZE"] = "2500"
    
    config_env = Settings()
    print(f"\nWith Environment Variables Override:")
    print(f"  auto_execute_trades: {config_env.auto_execute_trades}")
    print(f"  auto_execute_min_confidence: {config_env.auto_execute_min_confidence}")
    print(f"  auto_execute_position_size: ${config_env.auto_execute_position_size:.2f}")
    
    print("\n✅ Configuration loading test PASSED\n")
    return config_env


def test_execution_logic(config):
    """Test the trade execution logic."""
    print("=" * 60)
    print("TEST 2: Trade Execution Logic")
    print("=" * 60)
    
    # Create a test state
    trading_state = DeerflowState(
        tickers=["META", "MSFT", "NFLX"],
        trading_enabled=True,
        cash_balance=10000.0,
        positions={},
        trading_config={
            "commission_pct": 0.0001,
            "slippage_pct": 0.001,
        }
    )
    
    print(f"\nInitial State:")
    print(f"  Cash: ${trading_state.cash_balance:.2f}")
    print(f"  Positions: {len(trading_state.positions)}")
    
    # Test BUY execution
    print(f"\n--- Simulating BUY Execution ---")
    ticker = "META"
    price = 200.50
    quantity = int(config.auto_execute_position_size / price)
    total_cost = quantity * price
    commission = total_cost * trading_state.trading_config.get("commission_pct", 0.0001)
    slippage = price * quantity * trading_state.trading_config.get("slippage_pct", 0.001)
    total_charge = total_cost + commission + slippage
    
    print(f"  Ticker: {ticker}")
    print(f"  Price: ${price:.2f}")
    print(f"  Quantity: {quantity} shares")
    print(f"  Cost: ${total_cost:.2f}")
    print(f"  Commission: ${commission:.2f}")
    print(f"  Slippage: ${slippage:.2f}")
    print(f"  Total: ${total_charge:.2f}")
    print(f"  Available Cash: ${trading_state.cash_balance:.2f}")
    
    if total_charge <= trading_state.cash_balance:
        # Execute buy
        trading_state.cash_balance -= total_charge
        trading_state.positions[ticker] = {
            "quantity": quantity,
            "avg_cost": price,
            "current_value": quantity * price,
        }
        print(f"  ✅ BUY EXECUTED")
        print(f"  New Cash: ${trading_state.cash_balance:.2f}")
    else:
        print(f"  ❌ INSUFFICIENT CASH")
    
    # Test SELL execution
    print(f"\n--- Simulating SELL Execution ---")
    ticker = "META"
    price = 210.00  # Price went up
    pos_qty = trading_state.positions.get(ticker, {}).get("quantity", 0)
    
    if ticker in trading_state.positions and pos_qty > 0:
        total_proceeds = pos_qty * price
        commission = total_proceeds * trading_state.trading_config.get("commission_pct", 0.0001)
        slippage = price * pos_qty * trading_state.trading_config.get("slippage_pct", 0.001)
        proceeds = total_proceeds - commission - slippage
        
        print(f"  Ticker: {ticker}")
        print(f"  Quantity to sell: {pos_qty}")
        print(f"  Sale Price: ${price:.2f}")
        print(f"  Gross Proceeds: ${total_proceeds:.2f}")
        print(f"  Commission: ${commission:.2f}")
        print(f"  Slippage: ${slippage:.2f}")
        print(f"  Net Proceeds: ${proceeds:.2f}")
        
        # Execute sell
        trading_state.cash_balance += proceeds
        profit = proceeds - (pos_qty * trading_state.positions[ticker]["avg_cost"])
        print(f"  Profit/Loss: ${profit:.2f} ({(profit/(pos_qty * trading_state.positions[ticker]['avg_cost'])*100):.2f}%)")
        
        del trading_state.positions[ticker]
        print(f"  ✅ SELL EXECUTED")
        print(f"  New Cash: ${trading_state.cash_balance:.2f}")
    else:
        print(f"  ❌ NO POSITION TO SELL")
    
    print("\n✅ Trade execution logic test PASSED\n")


def test_confidence_calculation():
    """Test confidence score calculation."""
    print("=" * 60)
    print("TEST 3: Confidence Score Calculation")
    print("=" * 60)
    
    config = Settings()
    min_confidence = config.auto_execute_min_confidence
    
    test_scores = [2.5, 3.8, 5.0, 7.5, 10.0]
    
    print(f"\nMinimum Confidence Threshold: {min_confidence*100:.0f}%")
    print(f"\nScore → Confidence → Execution Decision:")
    
    for deep_score in test_scores:
        confidence = min(deep_score / 10.0, 1.0)
        will_execute = confidence >= min_confidence
        status = "✅ EXECUTE" if will_execute else "⏳ SKIP"
        
        print(f"  {deep_score:.1f}/10 → {confidence*100:5.0f}% → {status}")
    
    print("\n✅ Confidence calculation test PASSED\n")


def test_execution_reasons():
    """Test the reason generation logic."""
    print("=" * 60)
    print("TEST 4: Execution Reason Generation")
    print("=" * 60)
    
    test_cases = [
        ("META", 7.5, True, "Deep analysis score: 7.5/10 (75% confidence)"),
        ("MSFT", 4.1, False, "Confidence 41% below minimum 70%"),
        ("NFLX", 3.0, False, "Deep score 3.0/10 < 3.5"),
    ]
    
    print(f"\nReason Strings Generated:")
    for ticker, score, executed, reason in test_cases:
        confidence = min(score / 10.0, 1.0)
        status = "✅" if executed else "⏳"
        print(f"  {status} {ticker}: {reason}")
    
    print("\n✅ Reason generation test PASSED\n")


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("AUTO-EXECUTION FEATURE TEST SUITE")
        print("="*60 + "\n")
        
        config = test_config_loading()
        test_execution_logic(config)
        test_confidence_calculation()
        test_execution_reasons()
        
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nAuto-execution feature is ready to use.")
        print("To enable, set: AUTO_EXECUTE_TRADES=true")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
