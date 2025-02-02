from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TrafficData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    intersection_id = db.Column(db.String(50))
    traffic_density = db.Column(db.String(20))
    emergency_vehicle = db.Column(db.Boolean)
    time_of_day = db.Column(db.String(20))
    decision = db.Column(db.JSON)