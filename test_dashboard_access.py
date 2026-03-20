#!/usr/bin/env python
"""
Test script to verify Flask dashboard is accessible.
Run this after starting web_dashboard_trading.py
"""

import socket
import sys
import time
import urllib.request
import urllib.error

def test_port_open(host='127.0.0.1', port=5000, timeout=3):
    """Test if port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def test_http_accessible(url='http://127.0.0.1:5000/', timeout=3):
    """Test if HTTP endpoint is accessible"""
    try:
        response = urllib.request.urlopen(url, timeout=timeout)
        return response.status == 200 and len(response.read()) > 0
    except urllib.error.URLError as e:
        return False
    except Exception as e:
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Flask Dashboard Accessibility Test")
    print("=" * 60)
    
    print("\n1. Checking if port 5000 is open...")
    if test_port_open():
        print("   ✓ Port 5000 is OPEN")
    else:
        print("   ✗ Port 5000 is CLOSED")
        print("\n   Make sure you have run: python web_dashboard_trading.py")
        sys.exit(1)
    
    print("\n2. Checking if Flask is responding...")
    if test_http_accessible():
        print("   ✓ Flask is RESPONDING")
    else:
        print("   ✗ Flask is NOT responding")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ SUCCESS! Dashboard is accessible at:")
    print("   http://127.0.0.1:5000/")
    print("=" * 60)
    print("\nYou can now:")
    print("  • Open the URL in your browser")
    print("  • Use the API endpoints (e.g., /api/portfolio, /api/trades)")
    print("  • View real-time trading data")
