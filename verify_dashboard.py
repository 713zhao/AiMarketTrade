"""Verify Flask dashboard is working"""
import socket
import time
import subprocess
import sys
from pathlib import Path

def is_port_open(port, host='127.0.0.1', timeout=3):
    """Check if a port is open using socket"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        is_open = result == 0
        sock.close()
        return is_open
    except:
        return False

print("Starting Flask dashboard...")
print("-" * 60)

# Start the Flask app
proc = subprocess.Popen(
    [sys.executable, "web_dashboard_trading.py"],
    cwd=Path(__file__).parent,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Give it time to start
print("Waiting for Flask to initialize...", end="", flush=True)
for i in range(20):  # 20 seconds timeout
    time.sleep(0.5)
    if is_port_open(5000):
        print(" ✓ SUCCESS!")
        print(f"Dashboard is accessible at http://127.0.0.1:5000/")
        break
    print(".", end="", flush=True)
else:
    print(" ✗ FAILED!")
    print("Port 5000 is not open after 10 seconds")

    # Try to get output
    try:
        stdout, stderr = proc.communicate(timeout=2)
        if stderr:
            print("\nError output:")
            print(stderr[:500])
    except:
        pass

# Clean up
proc.terminate()
try:
    proc.wait(timeout=2)
except:
    proc.kill()

print("-" * 60)
