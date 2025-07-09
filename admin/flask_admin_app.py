# coding: utf-8
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kuzkabuh.db'
db = SQLAlchemy(app)

class Zayavki(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.DateTime, default=datetime.now)
    Inn = db.Column(db.String(12))
    Email = db.Column(db.String(120))
    Phone = db.Column(db.String(25))
    Name = db.Column(db.String(50))
    Contact_Time = db.Column(db.String(40))
    Service = db.Column(db.String(80))
    Urgency = db.Column(db.String(30))

admin = Admin(app, name="BUH.KUZKA", template_mode='bootstrap4')
admin.add_view(ModelView(Zayavki, db.session))

@app.route('/api/add_order', methods=['POST'])
def api_add_order():
    data = request.json
    z = Zayavki(
        Date=datetime.now(),
        Inn=data["inn"],
        Email=data["email"],
        Phone=data["phone"],
        Name=data["name"],
        Contact_Time=f"{data['contact_date']} {data['contact_time']}",
        Service=data["service"],
        Urgency=data["urgency"]
    )
    db.session.add(z)
    db.session.commit()
    return jsonify({"ok": True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=59000)
