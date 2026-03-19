# Trading Scanner Algorithm - Test Suite Guide

This directory contains comprehensive end-to-end tests for the stock trading scanner algorithm. These tests help ensure the algorithm is working correctly and catch any regressions from code changes.

## Test Files

### 1. **test_scanner_e2e.py** - Core Algorithm Unit Tests
Tests individual components and signal detection logic with mocked data.

**Test Classes:**
- `TestSignalDetection` - RSI, MACD, volume spike calculations
- `TestRecommendationScoring` - BUY/SELL/HOLD scoring logic
- `TestReasonFieldPopulation` - Signal reason descriptions
- `TestMarketHours` - Market open/close checking
- `TestIndustryScan` - Full industry scan operations
- `TestBackgroundScanner` - Background scanner caching
- `TestDataPersistence` - JSON file storage
- `TestIntegrationScenarios` - Multi-industry workflows

**Run:**
```bash
# Run all e2e tests
pytest tests/test_scanner_e2e.py -v

# Run specific test class
pytest tests/test_scanner_e2e.py::TestSignalDetection -v

# Run with detailed output
pytest tests/test_scanner_e2e.py -v -s
```

### 2. **test_scanner_smoke.py** - Integration Tests with Real Data
Full end-to-end tests that run actual yfinance scans to verify the complete pipeline.

**Test Classes:**
- `TestScannerSmokeTests` - Real data scans for each industry
- `TestRealScanResults` - Validation of scan result files

**Important:** These tests are marked with `@pytest.mark.slow` because they fetch real data from Yahoo Finance. This is intentional - they verify the algorithm actually works with real market data.

**Run:**
```bash
# Run smoke tests (with real yfinance data)
pytest tests/test_scanner_smoke.py -v -s

# Run specific smoke test
pytest tests/test_scanner_smoke.py::TestScannerSmokeTests::test_tech_industry_full_scan -v -s

# Run only quick tests (skip smoke tests)
pytest tests/ -v -m "not slow"

# Run all tests including smoke
pytest tests/ -v
```

### 3. **test_api_integration.py** - Flask API & Dashboard Tests
Tests that the web dashboard API endpoints work correctly with scanner data.

**Test Classes:**
- `TestAPIEndpoints` - Individual endpoint functionality
- `TestDataFallback` - Data caching and file fallback logic
- `TestResponseStructure` - API response validation
- `TestIntegrationScenarios` - Dashboard page loading
- `TestScannerDataConsistency` - Data integrity
- `TestErrorHandling` - Error handling
- `TestConcurrency` - Concurrent API access

**Run:**
```bash
# Run API tests
pytest tests/test_api_integration.py -v

# Run specific test
pytest tests/test_api_integration.py::TestAPIEndpoints::test_scanner_status_endpoint -v
```

## Running All Tests

### Quick Test Run (No Real Data)
```bash
# Run all tests except slow/smoke tests (uses mocked data)
pytest tests/ -v -m "not slow"

# Run only unit tests
pytest tests/test_scanner_e2e.py tests/test_api_integration.py -v
```

### Full Test Run (With Real Data)
```bash
# Run everything including real yfinance scans
pytest tests/ -v -s

# Run everything with coverage report
pytest tests/ --cov=src --cov=web_dashboard_trading -v
```

### Targeted Test Runs
```bash
# Test signal detection
pytest tests/ -k "signal" -v

# Test market hours
pytest tests/ -k "market_hours" -v

# Test reason fields
pytest tests/ -k "reason" -v

# Test API endpoints  
pytest tests/ -k "endpoint" -v
```

## What Each Test Suite Validates

### Algorithm Correctness
✅ **RSI Calculation** - Detects oversold (<30) and overbought (>70) conditions
✅ **MACD Analysis** - Generates buy/sell signals from MACD crossovers
✅ **Volume Spikes** - Identifies unusual trading volume (>1.5x average)
✅ **Signal Scoring** - Correctly scores and combines multiple signals
✅ **Recommendations** - Generates BUY/SELL/HOLD based on total score

### Data Quality
✅ **Reason Fields** - Populated with signal descriptions (e.g., "RSI Oversold(+2)")
✅ **Score Ranges** - Validated as 0-10 for buy_score and sell_score
✅ **Result Structure** - All required fields present (ticker, price, rsi, etc.)
✅ **JSON Persistence** - Scan results properly saved and loadable

### Market Functionality
✅ **Market Hours** - Correctly checks if market is open
✅ **Multi-Market** - US, China, Hong Kong markets handled separately
✅ **Time Zones** - UTC hour calculations for trading hours
✅ **Scanner Loop** - Background scanner respects market hours

### API/Dashboard
✅ **Endpoint Status** - All endpoints return valid responses
✅ **Data Caching** - Results cached in memory for quick access
✅ **File Fallback** - Loads from JSON if cache is empty
✅ **Data Filtering** - `/recommendations` shows only BUY/SELL, `/all-results` shows all

## Expected Test Results

### Unit Tests (test_scanner_e2e.py)
- **Fast execution**: < 5 seconds
- **No external dependencies**: Uses mocked data
- **100% deterministic**: Same results every time
- **Low false positives**: Verifies algorithm logic

### Smoke Tests (test_scanner_smoke.py)
- **Slower execution**: 30-60 seconds (depends on yfinance)
- **Real data**: Fetches actual market data
- **Market dependent**: Results change based on current prices
- **Catches regressions**: Verifies algorithm works end-to-end
- **Occasional timeouts**: yfinance can be slow during high traffic

### API Tests (test_api_integration.py)
- **Medium execution**: 5-15 seconds
- **Requires Flask app**: Tests web endpoints
- **Multiple endpoints**: Tests complete API surface
- **Error handling**: Validates edge cases

## Interpreting Test Results

### ✅ All Tests Pass
```
====== test session starts ======
collected 47 items
tests/test_scanner_e2e.py ............................ PASSED
tests/test_scanner_smoke.py ........................... PASSED
tests/test_api_integration.py ......................... PASSED

====== 47 passed in 34.52s ======
```
**Meaning:** Algorithm is working correctly, no regressions detected.

### ⚠️ Smoke Tests Fail with Timeout
```
tests/test_scanner_smoke.py::TestScannerSmokeTests::test_full_industry_scan TIMEOUT
```
**Meaning:** yfinance is taking too long (common during high traffic). Try again later.

### ❌ Signal Detection Tests Fail
```
tests/test_scanner_e2e.py::TestSignalDetection::test_rsi_calculation_oversold FAILED
assert signal == "OVERSOLD" or signal is not None
```
**Meaning:** Signal calculation logic is broken. Check `src/data_fetcher.py` RSI implementation.

### ❌ Reason Field Tests Fail  
```
tests/test_scanner_e2e.py::TestReasonFieldPopulation::test_reason_field_populated_on_buy_signal FAILED
assert 'reason' in result  
```
**Meaning:** Reason field not populated. Check `scan_industry()` method in `src/data_fetcher.py`.

## Test Maintenance

### When to Run Tests

**Before pushing code:**
```bash
# Quick validation (< 10 seconds)
pytest tests/test_scanner_e2e.py tests/test_api_integration.py -v
```

**Before releasing:**
```bash
# Full test suite including real data (1-2 minutes)
pytest tests/ -v -s
```

**When modifying signal detection:**
```bash
# Run all signal-related tests
pytest tests/ -k "signal or momentum or macd or volume" -v
```

**When modifying API/dashboard:**
```bash
# Run API and integration tests
pytest tests/test_api_integration.py -v
```

### Adding New Tests

When adding new features, add corresponding tests:

1. **Algorithm changes** → Add to `test_scanner_e2e.py`
2. **Real data validation** → Add to `test_scanner_smoke.py`
3. **API changes** → Add to `test_api_integration.py`

Example:
```python
def test_new_signal_detection(self):
    """Test new signal detection logic."""
    with patch.object(DataFetcher, 'new_signal', return_value=True):
        results = DataFetcher.scan_industry("TECH")
        # Verify results
        assert len(results) > 0
        print("✓ New signal detection working")
```

## Troubleshooting

### Import errors on first run
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run from project root
cd c:\projects\ai\AiMarketTrade
pytest tests/
```

### yfinance timeout errors
```bash
# These are normal and expected. Try again or use -m "not slow"
pytest tests/ -m "not slow"
```

### API tests fail with "app not found"
```bash
# Make sure Flask app is running or can be imported
# Run from project root directory
cd c:\projects\ai\AiMarketTrade
pytest tests/test_api_integration.py -v
```

### Flaky test results
```bash
# Some tests depend on market hours and current prices
# Run multiple times to see if results are consistent
pytest tests/test_scanner_smoke.py -v --count=3
```

## Success Criteria

You know the tests are working well when:

✅ All `TestSignalDetection` tests pass consistently
✅ `TestMarketHours` validation is accurate  
✅ `TestReasonFieldPopulation` shows detailed signal reasons
✅ Smoke tests complete without timeouts
✅ API integration tests show all endpoints responding
✅ Multiple test runs produce consistent results

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Mocking](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Algorithm Details](../HOW_SIGNALS_ARE_DECIDED.md)
- [Implementation Guide](../IMPLEMENTATION_DETAILS.md)
