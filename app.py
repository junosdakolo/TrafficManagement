import os
import random
import time
from threading import Thread
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Database model
class TrafficData(db.Model):
    # ... (keep your existing model columns) ...

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace(
        'postgres://', 'postgresql://', 1
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Initialize tables
    with app.app_context():
        db.create_all()

    # Start thread only once
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        if not hasattr(app, 'background_thread'):
            app.background_thread = Thread(target=background_data_worker)
            app.background_thread.daemon = True
            app.background_thread.start()
            app.logger.info("🚦 Background thread started")

    # Routes
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/traffic_data')
    def get_traffic_data():
        records = TrafficData.query.order_by(TrafficData.id.desc()).limit(50).all()
        return jsonify([{
            # ... (your existing response format) ...
        } for r in records])

    return app

def background_data_worker():
    """Persistent background data generator"""
    while True:
        try:
            with app.app_context():
                # Your data generation logic
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
                app.logger.debug(f"Added record: {new_data['intersection_id']}")
        except Exception as e:
            app.logger.error(f"Background worker error: {str(e)}")
        time.sleep(5)

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)