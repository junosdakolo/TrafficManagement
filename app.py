from flask import Flask, jsonify, render_template
import pandas as pd
import random
import time
from threading import Thread

# Initialize Flask app
app = Flask(__name__)

# Simulated traffic data
traffic_data = pd.DataFrame(columns=["intersection_id", "traffic_density", "emergency_vehicle", "time_of_day"])

# Simulate traffic data generation
def generate_traffic_data():
    return {
        "intersection_id": random.choice(["Apapa", "Mile 2", "Ikeja", "Lekki", "Ikoyi", "Victoria Island"]),
        "traffic_density": random.choice(["low", "medium", "high"]),
        "emergency_vehicle": random.choice([True, False]),
        "time_of_day": random.choice(["morning_rush", "daytime", "evening_rush", "night"])
    }

# Rule-based decision logic for traffic management
def adjust_signal_timing(traffic_density):
    if traffic_density == "high":
        return "Increase green light duration by 30%"
    elif traffic_density == "medium":
        return "Normal signal timing"
    else:
        return "Decrease green light duration by 20%"

def prioritize_emergency(emergency_vehicle):
    if emergency_vehicle:
        return "Give priority, extend green light"
    else:
        return "No priority, maintain normal signal"

def adjust_for_time_of_day(time_of_day):
    if time_of_day == "morning_rush" or time_of_day == "evening_rush":
        return "Extend green light duration by 20%"
    else:
        return "Maintain normal signal timing"

# Expert system decision-making function
def traffic_management_decision(data):
    traffic_density_action = adjust_signal_timing(data["traffic_density"])
    emergency_action = prioritize_emergency(data["emergency_vehicle"])
    time_of_day_action = adjust_for_time_of_day(data["time_of_day"])

    return {
        "intersection_id": data["intersection_id"],
        "traffic_density": data["traffic_density"],
        "emergency_vehicle": data["emergency_vehicle"],
        "time_of_day": data["time_of_day"],
        "traffic_density_action": traffic_density_action,
        "emergency_action": emergency_action,
        "time_of_day_action": time_of_day_action
    }


# Background thread to simulate traffic data and decisions
def generate_data_in_background():
    global traffic_data
    while True:
        new_data = generate_traffic_data()
        traffic_data = pd.concat([traffic_data, pd.DataFrame([new_data])], ignore_index=True)
        decision = traffic_management_decision(new_data)
        time.sleep(5)

# Run the background thread
thread = Thread(target=generate_data_in_background)
thread.daemon = True
thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/traffic_data')
def get_traffic_data():
    decisions = [traffic_management_decision(row) for _, row in traffic_data.iterrows()]
    return jsonify(decisions)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

