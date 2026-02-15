from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# In-memory storage for sensor data
data = {
    "entered": 0,
    "departed": 0,
    "inside": 0
}

# Command flag (0 if reset requested, 1 otherwise)
command = 1

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
        return jsonify({"status": "success", "message": "Data updated"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(data)

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
