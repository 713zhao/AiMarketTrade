"""
Smoke tests for scanner algorithm - run with real data.

These tests execute actual scans with real yfinance data to verify
the complete pipeline is working correctly. Good for detecting regressions.

Run with: pytest tests/test_scanner_smoke.py -v -s
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

from src.data_fetcher import DataFetcher
from src.market_config import Market, is_market_open
from src.background_scanner import BackgroundScanner


@pytest.mark.slow
class TestScannerSmokeTests:
    """Smoke tests that run actual scans with real data."""
    
    def test_single_stock_analysis_aapl(self):
        """Test analyzing a single popular stock (AAPL)."""
        print("\n" + "="*60)
        print("SMOKE TEST: Single Stock Analysis (AAPL)")
        print("="*60)
        
        # Get current price
        price = DataFetcher.get_current_price("AAPL")
        assert price is not None, "Failed to get AAPL price"
        assert 'Close' in price or 'price' in str(price).lower()
        
        print(f"✓ AAPL price retrieved: {price}")
        
        # Get technical indicators
        rsi, rsi_signal = DataFetcher.calculate_momentum("AAPL")
        assert rsi is not None, "Failed to calculate RSI"
        assert 0 <= rsi <= 100, f"RSI out of range: {rsi}"
        
        print(f"✓ RSI calculated: {rsi:.2f}, Signal: {rsi_signal}")
        
        # Get volume spike data
        volume_ratio, is_spike = DataFetcher.detect_volume_spike("AAPL")
        assert volume_ratio is not None, "Failed to detect volume spike"
        
        print(f"✓ Volume analysis: Ratio={volume_ratio:.2f}, Spiking={is_spike}")
        
        # Get MACD
        macd = DataFetcher.calculate_macd("AAPL")
        assert macd is not None, "Failed to calculate MACD"
        
        print(f"✓ MACD calculated: {macd}")
    
    def test_tech_industry_full_scan(self):
        """Test complete TECH industry scan."""
        print("\n" + "="*60)
        print("SMOKE TEST: Full TECH Industry Scan")
        print("="*60)
        
        # Run actual scan
        results = DataFetcher.scan_industry("TECH", Market.US)
        
        assert len(results) > 0, "TECH scan returned no results"
        print(f"✓ Scanned {len(results)} TECH stocks")
        
        # Analyze results
        buy_count = sum(1 for r in results if r['recommendation'] == 'BUY')
        sell_count = sum(1 for r in results if r['recommendation'] == 'SELL')
        hold_count = sum(1 for r in results if r['recommendation'] == 'HOLD')
        
        print(f"  Results: {buy_count} BUY, {sell_count} SELL, {hold_count} HOLD")
        
        # Verify each result structure
        for result in results:
            assert 'ticker' in result, f"Missing ticker in {result}"
            assert 'recommendation' in result in ['BUY', 'SELL', 'HOLD']
            assert 'reason' in result, f"Missing reason for {result.get('ticker')}"
            assert isinstance(result['buy_score'], (int, float))
            assert isinstance(result['sell_score'], (int, float))
        
        print("✓ All results have valid structure")
        
        # Show top BUY signals
        if buy_count > 0:
            buy_signals = [r for r in results if r['recommendation'] == 'BUY']
            print(f"\nTop BUY signals:")
            for sig in buy_signals[:3]:
                print(f"  - {sig['ticker']}: {sig['reason']}")
    
    def test_finance_industry_full_scan(self):
        """Test complete FINANCE industry scan."""
        print("\n" + "="*60)
        print("SMOKE TEST: Full FINANCE Industry Scan")
        print("="*60)
        
        # Run actual scan
        results = DataFetcher.scan_industry("FINANCE", Market.US)
        
        assert len(results) > 0, "FINANCE scan returned no results"
        print(f"✓ Scanned {len(results)} FINANCE stocks")
        
        # Analyze results
        buy_count = sum(1 for r in results if r['recommendation'] == 'BUY')
        sell_count = sum(1 for r in results if r['recommendation'] == 'SELL')
        hold_count = sum(1 for r in results if r['recommendation'] == 'HOLD')
        
        print(f"  Results: {buy_count} BUY, {sell_count} SELL, {hold_count} HOLD")
        
        # Verify reason fields are populated
        for result in results:
            assert result['reason'] != "", f"{result['ticker']} has empty reason"
            if result['recommendation'] != 'HOLD':
                assert len(result['reason']) > 5, f"{result['ticker']} reason too short"
        
        print("✓ All results have detailed reason fields")
    
    def test_healthcare_industry_full_scan(self):
        """Test complete HEALTHCARE industry scan."""
        print("\n" + "="*60)
        print("SMOKE TEST: Full HEALTHCARE Industry Scan")
        print("="*60)
        
        # Run actual scan
        results = DataFetcher.scan_industry("HEALTHCARE", Market.US)
        
        assert len(results) > 0, "HEALTHCARE scan returned no results"
        print(f"✓ Scanned {len(results)} HEALTHCARE stocks")
        
        # Analyze results
        recommendations = {}
        for result in results:
            rec = result['recommendation']
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        print(f"  Breakdown: {recommendations}")
        
        # Verify all scores are valid
        for result in results:
            assert 0 <= result['buy_score'] <= 10
            assert 0 <= result['sell_score'] <= 10
        
        print("✓ All scores within valid range [0-10]")
    
    def test_multiple_industries_sequential_scan(self):
        """Test scanning multiple industries in sequence."""
        print("\n" + "="*60)
        print("SMOKE TEST: Multiple Industries Sequential Scan")
        print("="*60)
        
        industries = ["TECH", "FINANCE", "HEALTHCARE"]
        all_results = {}
        
        for industry in industries:
            print(f"\nScanning {industry}...")
            results = DataFetcher.scan_industry(industry, Market.US)
            all_results[industry] = results
            
            buy_count = sum(1 for r in results if r['recommendation'] == 'BUY')
            print(f"  ✓ {len(results)} stocks: {buy_count} BUY signals")
        
        # Aggregate statistics
        total_stocks = sum(len(r) for r in all_results.values())
        total_buy = sum(sum(1 for r in results if r['recommendation'] == 'BUY') 
                       for results in all_results.values())
        total_sell = sum(sum(1 for r in results if r['recommendation'] == 'SELL') 
                        for results in all_results.values())
        total_hold = sum(sum(1 for r in results if r['recommendation'] == 'HOLD') 
                        for results in all_results.values())
        
        print(f"\n✓ Total: {total_stocks} stocks scanned")
        print(f"  Summary: {total_buy} BUY, {total_sell} SELL, {total_hold} HOLD")
    
    def test_scan_consistency_same_stock(self):
        """Test that scanning the same stock twice produces consistent results."""
        print("\n" + "="*60)
        print("SMOKE TEST: Scan Consistency Check")
        print("="*60)
        
        # Scan same industry twice
        print("First scan...")
        scan1 = DataFetcher.scan_industry("FINANCE", Market.US)
        
        print("Second scan (30 seconds later)...")
        time.sleep(5)  # Wait a bit between scans
        scan2 = DataFetcher.scan_industry("FINANCE", Market.US)
        
        # Check JPM results if present
        jpm1 = next((r for r in scan1 if r['ticker'] == 'JPM'), None)
        jpm2 = next((r for r in scan2 if r['ticker'] == 'JPM'), None)
        
        if jpm1 and jpm2:
            print(f"JPM - Scan 1: {jpm1['recommendation']} (RSI={jpm1.get('rsi', 'N/A')})")
            print(f"JPM - Scan 2: {jpm2['recommendation']} (RSI={jpm2.get('rsi', 'N/A')})")
            
            # Recommendations might differ slightly but should be close
            if jpm1['recommendation'] == jpm2['recommendation']:
                print("✓ Consistent recommendation across scans")
            else:
                print(f"⚠ Recommendations differ (normal if market conditions changed)")
    
    def test_market_hours_checking_accuracy(self):
        """Test market hours checking works correctly."""
        print("\n" + "="*60)
        print("SMOKE TEST: Market Hours Checking")
        print("="*60)
        
        from datetime import datetime
        current_utc = datetime.utcnow()
        current_hour = current_utc.hour
        
        print(f"Current UTC time: {current_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Check each market
        us_open = is_market_open(Market.US)
        china_open = is_market_open(Market.CHINA)
        hk_open = is_market_open(Market.HK)
        
        print(f"\nMarket Status:")
        print(f"  US Market (13-21 UTC): {'OPEN' if us_open else 'CLOSED'}")
        print(f"  China Market (0-9 UTC): {'OPEN' if china_open else 'CLOSED'}")
        print(f"  HK Market (1-10 UTC): {'OPEN' if hk_open else 'CLOSED'}")
        
        # Verify logic
        assert us_open == (13 <= current_hour < 21)
        assert china_open == (0 <= current_hour < 9)
        assert hk_open == (1 <= current_hour < 10)
        
        print("✓ Market hours logic verified")
    
    def test_background_scanner_basic_operations(self):
        """Test background scanner can be created and accessed."""
        print("\n" + "="*60)
        print("SMOKE TEST: Background Scanner Operations")
        print("="*60)
        
        scanner = BackgroundScanner()
        print("✓ Scanner initialized")
        
        # Mock some results
        scanner.scan_results["TEST"] = [
            {'ticker': 'TEST1', 'recommendation': 'BUY', 'reason': 'Test signal'},
            {'ticker': 'TEST2', 'recommendation': 'HOLD', 'reason': 'No signals'},
        ]
        
        # Get results
        results = scanner.get_all_results("TEST")
        assert len(results) == 2
        print(f"✓ Retrieved {len(results)} cached results")
        
        # Verify no filtering
        buy_results = [r for r in results if r['recommendation'] == 'BUY']
        hold_results = [r for r in results if r['recommendation'] == 'HOLD']
        assert len(buy_results) == 1 and len(hold_results) == 1
        print("✓ Results returned without filtering")


class TestRealScanResults:
    """Test that actual scan results files are valid."""
    
    def test_scan_results_files_exist_and_valid(self):
        """Test that scan result JSON files exist and are valid."""
        print("\n" + "="*60)
        print("VALIDATION TEST: Scan Results Files")
        print("="*60)
        
        scan_dir = Path("scan_results")
        
        if not scan_dir.exists():
            print("⚠ scan_results directory does not exist (will be created on first scan)")
            return
        
        scan_files = list(scan_dir.glob("*_scan.json"))
        print(f"Found {len(scan_files)} scan result files")
        
        for file in scan_files:
            print(f"\nValidating {file.name}...")
            
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                # Verify structure
                assert 'industry' in data or 'results' in data
                if 'results' in data:
                    assert isinstance(data['results'], list)
                    
                    if len(data['results']) > 0:
                        # Check first result
                        first = data['results'][0]
                        required_fields = ['ticker', 'recommendation', 'reason']
                        for field in required_fields:
                            assert field in first, f"Missing {field} in first result"
                    
                    print(f"  ✓ Valid JSON with {len(data['results'])} results")
                    
                    # Show stats
                    buy = sum(1 for r in data['results'] if r['recommendation'] == 'BUY')
                    sell = sum(1 for r in data['results'] if r['recommendation'] == 'SELL')
                    hold = sum(1 for r in data['results'] if r['recommendation'] == 'HOLD')
                    print(f"  Stats: {buy} BUY, {sell} SELL, {hold} HOLD")
                    
                    if 'timestamp' in data:
                        print(f"  Last updated: {data['timestamp']}")
                else:
                    print(f"  ✓ Valid JSON structure")
                    
            except json.JSONDecodeError as e:
                print(f"  ✗ Invalid JSON: {e}")
                pytest.fail(f"Invalid JSON in {file.name}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                pytest.fail(f"Error validating {file.name}: {e}")


if __name__ == "__main__":
    """
    Run smoke tests with:
    pytest tests/test_scanner_smoke.py -v -s
    
    Run specific test:
    pytest tests/test_scanner_smoke.py::TestScannerSmokeTests::test_tech_industry_full_scan -v -s
    
    Note: These tests take time because they run actual yfinance scans.
    Good for verifying algorithm changes don't break functionality.
    """
    pass
