# Quick Test Reference

Common commands to run tests:

## Run Everything
```bash
pytest tests/ -v
```

## Run Quick Tests Only (No Real Data)
```bash
pytest tests/ -v -m "not slow"
```

## Run Specific Suite
```bash
# Unit tests with mocked data (fast)
pytest tests/test_scanner_e2e.py -v

# Integration tests with real yfinance data (slow)
pytest tests/test_scanner_smoke.py -v -s

# API endpoint tests
pytest tests/test_api_integration.py -v
```

## Run Specific Test
```bash
# Signal detection tests
pytest tests/test_scanner_e2e.py::TestSignalDetection -v

# TECH industry scan
pytest tests/test_scanner_smoke.py::TestScannerSmokeTests::test_tech_industry_full_scan -v -s

# API status endpoint
pytest tests/test_api_integration.py::TestAPIEndpoints::test_scanner_status_endpoint -v
```

## Run Tests by Topic
```bash
# All signal-related tests
pytest tests/ -k "signal" -v

# All market hours tests
pytest tests/ -k "market_hours" -v

# All reason field tests
pytest tests/ -k "reason" -v

# All API tests
pytest tests/ -k "endpoint" -v
```

## Generate Coverage Report
```bash
pytest tests/ --cov=src --cov=web_dashboard_trading --cov-report=html -v
# Opens coverage report in htmlcov/index.html
```

## Run with Detailed Output
```bash
pytest tests/ -v -s
```

## Run and Stop at First Failure
```bash
pytest tests/ -x -v
```

## Run Tests N Times
```bash
# Requires: pip install pytest-repeat
pytest tests/ --count=3 -v
```

## Expected Output

### Successful Run
```
========================= test session starts ==========================
collected 47 items

tests/test_scanner_e2e.py::TestSignalDetection::test_rsi_calculation_oversold PASSED
tests/test_scanner_e2e.py::TestSignalDetection::test_rsi_calculation_overbought PASSED
...
tests/test_api_integration.py::TestAPIEndpoints::test_scanner_status_endpoint PASSED

========================= 47 passed in 34.52s ==========================
```

## Test Descriptions

| Test | Time | Data | Purpose |
|------|------|------|---------|
| `test_scanner_e2e.py` | < 5s | Mocked | Verify signal detection logic |
| `test_scanner_smoke.py` | 30-60s | Real | Verify end-to-end with real prices |
| `test_api_integration.py` | 5-15s | Mock | Verify API endpoints work |

## Troubleshooting

**Import Error:** Run from project root: `cd c:\projects\ai\AiMarketTrade`

**Timeout:** Use `-m "not slow"` to skip real data tests

**App Not Found:** Make sure `web_dashboard_trading.py` exists and is importable

**Flaky Results:** Some tests depend on market hours; run multiple times

## Key Points

✅ Run unit tests before each code change
✅ Run smoke tests before releasing
✅ Check reason fields are populated
✅ Verify all industries scan correctly
✅ Test market hours checking
✅ Validate API endpoints
