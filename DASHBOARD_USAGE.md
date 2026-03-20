# How to Run the Flask Dashboard

## Quick Start (Using Virtual Environment)

### On Windows PowerShell:

```powershell
# 1. Navigate to the project directory
cd c:\projects\ai\AiMarketTrade

# 2. Activate virtual environment (if not already activated)
.\.venv\Scripts\Activate.ps1

# 3. Run the dashboard
python web_dashboard_trading.py
```

Or use the Python executable directly from venv:

```powershell
cd c:\projects\ai\AiMarketTrade
.\.venv\Scripts\python.exe web_dashboard_trading.py
```

## What to Expect

The dashboard will print:
```
============================================================
Trading System Dashboard
============================================================
Dashboard URL: http://127.0.0.1:5000
============================================================
Starting Flask server...
 * Serving Flask app 'web_dashboard_trading'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

## Access the Dashboard

Open your browser to: **http://127.0.0.1:5000/**

## Troubleshooting

### Port Already in Use
If you get "Address already in use" error:

```powershell
# Kill the process using port 5000
taskkill /F /IM python.exe

# Or kill a specific PID
taskkill /PID 12345 /F

# Then try again
.\.venv\Scripts\python.exe web_dashboard_trading.py
```

### Flask Import Errors
Make sure you're using the virtual environment:

```powershell
# Check which Python is being used
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
# Should show path with .venv\Lib

# Check Flask version
.\.venv\Scripts\python.exe -c "import flask; print(flask.__version__)"
```

### Can't Access Dashboard
1. Wait 5-10 seconds for initialization to complete
2. Check port 5000 is listening: `netstat -ano | findstr 5000`
3. Try accessing from browser or PowerShell:
   ```powershell
   # From PowerShell
   Invoke-WebRequest -Uri http://127.0.0.1:5000/ -TimeoutSec 5
   ```

## Fixed Issues

✅ **Flask Version Compatibility** - Removed unsupported `include_werkzeug_logger` parameter
✅ **Virtual Environment** - Uses .venv Python explicitly  
✅ **Port Conflicts** - Auto-fallback to ports 5001-5009 if 5000 in use
✅ **Datetime Deprecation** - Updated to use `datetime.now(timezone.utc)`
✅ **Threading Issues** - Initialization runs in background thread

## Environment Details

- **Python Location**: `.\.venv\Scripts\python.exe`
- **Flask**: Latest version installed in venv
- **Port**: 5000 (or 5001+ if 5000 unavailable)
- **Host**: 127.0.0.1 (localhost only)
- **Threading**: Enabled for concurrent requests
- **Debug Mode**: Off (production ready)
