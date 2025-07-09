from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Zayavka(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False)
    inn = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    contact_name = db.Column(db.String(100))
    time_to_call = db.Column(db.String(50))
    service = db.Column(db.String(100))
    urgent = db.Column(db.String(10))
