import os
import random
import time
import logging
from threading import Thread
from datetime import datetime
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configure database with environment variables
    db_url = "postgresql://traffic_user:cHmp4FxmJf7cUAyvEoshCIdq3zJjDH9j@dpg-cufv9lan91rc73ckae2g-a/trafficdb_vxts"

    
    # Fix common PostgreSQL URL issues
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    # Add SSL requirement for production
    if 'postgresql' in db_url and '?sslmode=' not in db_url:
        db_url += '?sslmode=require'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300
    }

    # Initialize database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()

    # Configure background thread (Render-safe)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        if not hasattr(app, 'background_thread_started'):
            app.background_thread_started = True
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
        try:
            records = TrafficData.query.order_by(TrafficData.timestamp.desc()).limit(50).all()
            return jsonify([{
                'intersection_id': r.intersection_id,
                'traffic_density': r.traffic_density,
                'emergency_vehicle': r.emergency_vehicle,
                'time_of_day': r.time_of_day,
                'decision': r.decision,
                'timestamp': r.timestamp.isoformat()
            } for r in records])
        except Exception as e:
            app.logger.error(f"Error fetching data: {str(e)}")
            return jsonify({"error": "Failed to retrieve data"}), 500

    @app.route('/dbcheck')
    def db_check():
        try:
            db.session.execute("SELECT 1")
            return "Database connection successful", 200
        except Exception as e:
            app.logger.error(f"Database connection failed: {str(e)}")
            return f"Database connection failed: {str(e)}", 500

    return app

# Database Model
class TrafficData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    intersection_id = db.Column(db.String(50), nullable=False)
    traffic_density = db.Column(db.String(20), nullable=False)
    emergency_vehicle = db.Column(db.Boolean, nullable=False)
    time_of_day = db.Column(db.String(20), nullable=False)
    decision = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

# Data Generation Functions
def generate_traffic_data():
    return {
        "intersection_id": random.choice([
            "Apapa", "Mile 2", "Ikeja", 
            "Lekki", "Ikoyi", "Victoria Island"
        ]),
        "traffic_density": random.choice(["low", "medium", "high"]),
        "emergency_vehicle": random.choice([True, False]),
        "time_of_day": random.choice([
            "morning_rush", "daytime", 
            "evening_rush", "night"
        ])
    }

def traffic_management_decision(data):
    return {
        "traffic_density_action": (
            "Increase green by 30%" if data["traffic_density"] == "high" else
            "Normal" if data["traffic_density"] == "medium" else
            "Decrease by 20%"
        ),
        "emergency_action": (
            "Priority extended green" 
            if data["emergency_vehicle"] 
            else "Normal"
        ),
        "time_of_day_action": (
            "Extend green by 20%" 
            if data["time_of_day"] in ["morning_rush", "evening_rush"] 
            else "Normal"
        )
    }

def generate_data_in_background():
    while True:
        try:
            with app.app_context():
                new_data = generate_traffic_data()
                decision = traffic_management_decision(new_data)
                record = TrafficData(
                    intersection_id=new_data["intersection_id"],
                    traffic_density=new_data["traffic_density"],
                    emergency_vehicle=new_data["emergency_vehicle"],
                    time_of_day=new_data["time_of_day"],
                    decision=decision
                )
                db.session.add(record)
                db.session.commit()
                app.logger.debug(f"Record added: {new_data['intersection_id']}")
        except Exception as e:
            app.logger.error(f"Background data error: {str(e)}")
            db.session.rollback()
        time.sleep(5)

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)