import sys
result = True
try:
    from flask import Flask
    app = Flask(__name__)
    print("FLASK_OK")
except Exception as e:
    print(f"ERROR:{str(e)[:100]}")
    result = False
