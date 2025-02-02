import os
import random
import time
from threading import Thread
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Database model must be defined first
class TrafficData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    intersection_id = db.Column(db.String(50))
    traffic_density = db.Column(db.String(20))
    emergency_vehicle = db.Column(db.Boolean)
    time_of_day = db.Column(db.String(20))
    decision = db.Column(db.JSON)

# Data generation functions next
def generate_traffic_data():
    return {
        "intersection_id": random.choice(["Apapa", "Mile 2", "Ikeja", "Lekki", "Ikoyi", "Victoria Island"]),
        "traffic_density": random.choice(["low", "medium", "high"]),
        "emergency_vehicle": random.choice([True, False]),
        "time_of_day": random.choice(["morning_rush", "daytime", "evening_rush", "night"])
    }

def traffic_management_decision(data):
    return {
        "traffic_density_action": "Increase green by 30%" if data["traffic_density"] == "high" else 
                                "Normal" if data["traffic_density"] == "medium" else 
                                "Decrease by 20%",
        "emergency_action": "Priority extended green" if data["emergency_vehicle"] else "Normal",
        "time_of_day_action": "Extend green by 20%" if data["time_of_day"] in ["morning_rush", "evening_rush"] 
                            else "Normal"
    }

# Then create the Flask app factory
def create_app():
    app = Flask(__name__)
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://', 1
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Configure background thread
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        thread = Thread(target=generate_data_in_background)
        thread.daemon = True
        thread.start()
        app.logger.info("🚦 Background data generation started")

    # Routes
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/traffic_data')
    def get_traffic_data():
        records = TrafficData.query.all()
        return jsonify([{
            'intersection_id': r.intersection_id,
            'traffic_density': r.traffic_density,
            'emergency_vehicle': r.emergency_vehicle,
            'time_of_day': r.time_of_day,
            'decision': r.decision
        } for r in records])

    return app

# Background process function last
def generate_data_in_background():
    while True:
        new_data = generate_traffic_data()
        decision = traffic_management_decision(new_data)
        with app.app_context():
            record = TrafficData(
                intersection_id=new_data["intersection_id"],
                traffic_density=new_data["traffic_density"],
                emergency_vehicle=new_data["emergency_vehicle"],
                time_of_day=new_data["time_of_day"],
                decision=decision
            )
            db.session.add(record)
            db.session.commit()
        time.sleep(5)

# Initialize Flask app
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)