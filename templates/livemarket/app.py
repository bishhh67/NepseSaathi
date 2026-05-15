from flask import Flask, send_from_directory, request, jsonify
import subprocess
import os
import sys

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/scrape')
def api_scrape():
    """Triggers the scraper using the same Python executable as the server."""
    try:
        print(f"Executing: {sys.executable} scrap_all.py")
        # Using sys.executable ensures it works inside virtual environments (.venv)
        process = subprocess.run([sys.executable, 'scrap_all.py'], capture_output=True, text=True)
        
        if process.returncode == 0:
            return jsonify({"status": "success", "message": "Latest data synced"})
        else:
            error_msg = process.stderr or "Unknown Scraper Error"
            print(f"Scraper Error: {error_msg}")
            return jsonify({"status": "error", "message": error_msg}), 500
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("NEPSE SATHI DASHBOARD")
    print(f"Running on Python: {sys.executable}")
    print("Open: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(port=5000)
