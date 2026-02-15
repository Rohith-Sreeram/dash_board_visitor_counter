from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import datetime
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app)

# Initialize Firebase
# Make sure to place your 'serviceAccountKey.json' in the root directory
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    print("⚠️ Warning: serviceAccountKey.json not found. Firebase will not be initialized.")
    db = None

# In-memory storage for sensor data (fallback/cache)
data = {
    "entered": 0,
    "departed": 0,
    "inside": 0
}

# Command flag (0 if reset requested, 1 otherwise)
command = 1

def load_latest_data():
    global data
    if not db:
        return
    try:
        # Get the latest document from counts to restore state
        docs = db.collection('counts').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()
        if docs:
            latest = docs[0].to_dict()
            data["entered"] = latest.get("entered", 0)
            data["departed"] = latest.get("departed", 0)
            data["inside"] = latest.get("inside", 0)
            print(f"🔄 Loaded latest data from Firebase: {data}")
    except Exception as e:
        print(f"⚠️ Could not load latest data: {e}")

load_latest_data()

def log_data(e, d, i):
    if not db:
        print("❌ Firebase not initialized. Skipping log.")
        return
    
    try:
        # Unique timestamp for plotting
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Log to Firestore
        doc_ref = db.collection('counts').document(timestamp_str)
        doc_ref.set({
            'timestamp': now,
            'entered': e,
            'departed': d,
            'inside': i
        })
        
        # Cleanup old data (Keep last 100 records for performance in this simple version)
        # In a real app, you'd use a scheduled task or a more sophisticated query
    except Exception as err:
        print(f"❌ Error logging to Firebase: {err}")

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
    if not db:
        print("❌ Firebase not initialized.")
        return jsonify({"labels": [], "values": []})
    
    try:
        # Get last 50 records to keep chart clean
        # Use .get() instead of .stream() because limit_to_last doesn't support streaming
        docs = db.collection('counts').order_by('timestamp', direction=firestore.Query.ASCENDING).limit_to_last(50).get()
        
        labels = []
        values = []
        count = 0
        for doc in docs:
            d = doc.to_dict()
            ts = d.get('timestamp')
            if ts:
                # Firestore timestamps are datetime objects
                labels.append(ts.strftime("%H:%M:%S"))
            else:
                labels.append(str(doc.id))
            values.append(int(d.get('inside', 0)))
            count += 1
            
        return jsonify({"labels": labels, "values": values})
    except Exception as err:
        print(f"❌ Error fetching history: {err}")
        return jsonify({"labels": [], "values": [], "error": str(err)})

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
