from flask import Flask, jsonify, render_template
import pandas as pd
import random
import time
from threading import Thread, Lock

app = Flask(__name__)

# Use a lock for thread-safe operations on shared data
data_lock = Lock()
traffic_data = pd.DataFrame(columns=["intersection_id", "traffic_density", "emergency_vehicle", "time_of_day"])

def generate_traffic_data():
    return {
        "intersection_id": random.choice(["Apapa", "Mile 2", "Ikeja", "Lekki", "Ikoyi", "Victoria Island"]),
        "traffic_density": random.choice(["low", "medium", "high"]),
        "emergency_vehicle": random.choice([True, False]),
        "time_of_day": random.choice(["morning_rush", "daytime", "evening_rush", "night"])
    }

def adjust_signal_timing(traffic_density):
    if traffic_density == "high":
        return "Increase green light duration by 30%"
    elif traffic_density == "medium":
        return "Normal signal timing"
    else:
        return "Decrease green light duration by 20%"

def prioritize_emergency(emergency_vehicle):
    return "Give priority, extend green light" if emergency_vehicle else "No priority, maintain normal signal"

def adjust_for_time_of_day(time_of_day):
    if time_of_day in ["morning_rush", "evening_rush"]:
        return "Extend green light duration by 20%"
    return "Maintain normal signal timing"

def traffic_management_decision(data):
    return {
        "intersection_id": data["intersection_id"],
        "traffic_density": data["traffic_density"],
        "emergency_vehicle": data["emergency_vehicle"],
        "time_of_day": data["time_of_day"],
        "traffic_density_action": adjust_signal_timing(data["traffic_density"]),
        "emergency_action": prioritize_emergency(data["emergency_vehicle"]),
        "time_of_day_action": adjust_for_time_of_day(data["time_of_day"])
    }

def generate_data_in_background():
    global traffic_data
    while True:
        new_data = generate_traffic_data()
        decision = traffic_management_decision(new_data)
        # Include the decision directly in the stored data
        with data_lock:
            new_record = {**new_data, "decision": decision}
            traffic_data = pd.concat([traffic_data, pd.DataFrame([new_record])], ignore_index=True)
        time.sleep(5)

thread = Thread(target=generate_data_in_background)
thread.daemon = True
thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/traffic_data')
def get_traffic_data():
    with data_lock:
        # Convert DataFrame to a list of dictionaries and extract the decision
        decisions = [row["decision"] for _, row in traffic_data.iterrows()]
    return jsonify(decisions)

if __name__ == '__main__':
    app.run(debug=True, port=5000)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))