"""
Fresh test script to launch Flask and check if it's accessible
"""
import subprocess
import time
import socket

def is_port_listening(port, host='127.0.0.1'):
    """Check if port is listening"""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

print("=" * 60)
print("Fresh Flask Test")
print("=" * 60)
print()

# Kill all existing Python processes
print("1. Killing existing Python processes...")
subprocess.run("taskkill /F /IM python.exe /T 2>nul", shell=True, capture_output=True)
time.sleep(2)

# Run Flask
print("2. Starting Flask with venv...")
proc = subprocess.Popen(
    [".venv\\Scripts\\python.exe", "web_dashboard_trading.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1  # Line buffered
)

# Wait for Flask to start and print first available message
print("3. Waiting for Flask to start...")
time.sleep(3)

# Check ports
print("4. Checking if Flask is listening...")
for port in [5000, 5001, 5002]:
    if is_port_listening(port):
        print(f"\n✓ SUCCESS! Flask IS listening on port {port}")
        print(f"\nAccess the dashboard at: http://127.0.0.1:{port}/")
        break
else:
    print("\n✗ Flask is NOT listening on any expected port")
    print("\nFlask output so far:")
    try:
        stdout_data = proc.communicate(timeout=2)[0]
        for line in stdout_data.split('\n')[:20]:
            if line.strip():
                print(f"  {line}")
    except:
        pass

# Cleanup
proc.terminate()
try:
    proc.wait(timeout=2)
except:
    proc.kill()

print("\n" + "=" * 60)
