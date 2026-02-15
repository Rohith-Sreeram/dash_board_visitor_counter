from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import datetime
import os

app = Flask(__name__)

# In-memory storage for sensor data
data = {
    "entered": 0,
    "departed": 0,
    "inside": 0
}

# Command flag (0 if reset requested, 1 otherwise)
command = 1

def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS counts 
                 (timestamp DATETIME, entered INTEGER, departed INTEGER, inside INTEGER)''')
    conn.commit()
    conn.close()

init_db()

def log_data(e, d, i):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # Unique timestamp for plotting
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO counts VALUES (?, ?, ?, ?)", (now, e, d, i))
    # Keep only 24 hours of data (roughly 720 records if every 2 mins)
    c.execute("DELETE FROM counts WHERE timestamp < datetime('now', '-1 day')")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update', methods=['POST'])
def update():
    global data
    try:
        new_data = request.get_json()
        data["entered"] = new_data.get("entered", data["entered"])
        data["departed"] = new_data.get("departed", data["departed"])
        data["inside"] = new_data.get("inside", data["inside"])
        
        # Log to database on update
        log_data(data["entered"], data["departed"], data["inside"])
        
        return jsonify({"status": "success", "message": "Data updated"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(data)

@app.route('/history', methods=['GET'])
def get_history():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, inside FROM counts ORDER BY timestamp ASC")
    rows = c.fetchall()
    conn.close()
    
    # Format for Chart.js
    labels = [row[0] for row in rows]
    values = [row[1] for row in rows]
    
    return jsonify({"labels": labels, "values": values})

@app.route('/reset', methods=['POST'])
def reset():
    global command
    command = 0
    return jsonify({"status": "success", "message": "Reset command sent"}), 200

@app.route('/get_command', methods=['GET'])
def get_command():
    global command
    current_command = command
    # Reset command back to 1 after it has been read once (optional, depends on ESP32 logic)
    # For now, let's keep it 0 until ESP32 acknowledges or until user resets again.
    # However, standard practice is often to reset the flag once polled.
    if command == 0:
        command = 1
    return str(current_command)

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
