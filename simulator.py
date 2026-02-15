import requests
import time
import random

# Configuration
# SERVER_URL = "https://dash-board-visitor-counter.onrender.com"
SERVER_URL = "http://127.0.0.1:5001"
UPDATE_ENDPOINT = f"{SERVER_URL}/update"
COMMAND_ENDPOINT = f"{SERVER_URL}/get_command"

def simulate_iot_device():
    print(f"🚀 Starting ESP32 Simulator... Target: {SERVER_URL}")
    
    # Initial state
    entered = 0
    departed = 0
    
    try:
        while True:
            # 1. Simulate sensor logic
            # Randomly increase entered or departed
            if random.random() > 0.7:
                entered += random.randint(1, 3)
            
            if random.random() > 0.8 and (entered > departed):
                departed += random.randint(1, 2)
                
            inside = entered - departed
            
            # 2. Send data to Dashboard
            payload = {
                "entered": entered,
                "departed": departed,
                "inside": inside
            }
            
            try:
                response = requests.post(UPDATE_ENDPOINT, json=payload, timeout=2)
                if response.status_code == 200:
                    print(f"✅ Data Sent: In: {entered} | Out: {departed} | Inside: {inside}")
                else:
                    print(f"❌ Server Error: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Connection Error: Is the Flask app running on {SERVER_URL}?")

            # 3. Poll for Reset Command (0) from Dashboard
            try:
                cmd_response = requests.get(COMMAND_ENDPOINT, timeout=2)
                if cmd_response.text == "0":
                    print("♻️  RESET COMMAND RECEIVED! Clearing counters...")
                    entered = 0
                    departed = 0
                    inside = 0
                    # Send cleared data immediately
                    requests.post(UPDATE_ENDPOINT, json={"entered": 0, "departed": 0, "inside": 0})
            except Exception as e:
                pass # Silently fail command polling if server is down

            time.sleep(2) # Wait 2 seconds before next update

    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped.")

simulate_iot_device()
