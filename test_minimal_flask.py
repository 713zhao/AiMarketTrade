"""
Minimal Flask app to test if Flask is working properly
"""
from flask import Flask

print("Creating Flask app...")
app = Flask(__name__)

@app.route('/')
def hello():
    return {'status': 'OK', 'message': 'Flask is working!'}

if __name__ == '__main__':
    print("Starting minimal Flask server on http://127.0.0.1:5000")
    print("="*60)
    try:
        app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
