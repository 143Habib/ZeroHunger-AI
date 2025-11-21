from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    full_name = db.Column(db.String(150))
    dietary_pref = db.Column(db.String(100), default="None") 
    location = db.Column(db.String(100))
    
    sdg_score = db.Column(db.Integer, default=50)
    total_money_saved = db.Column(db.Float, default=0.0)
    total_money_wasted = db.Column(db.Float, default=0.0)
    
    inventory = db.relationship('Inventory', backref='user', lazy=True)
    logs = db.relationship('ConsumptionLog', backref='user', lazy=True)
    shared_items = db.relationship('SharedItem', backref='user', lazy=True)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    category = db.Column(db.String(50))
    expiration_date = db.Column(db.DateTime)
    price = db.Column(db.Float, default=0.0)
    calories = db.Column(db.Integer, default=0)

class ConsumptionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    status = db.Column(db.String(20)) # "Consumed" or "Wasted"
    price = db.Column(db.Float, default=0.0)
    date_logged = db.Column(db.DateTime, default=datetime.utcnow)

class SharedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(100))
    description = db.Column(db.String(200))
    contact_info = db.Column(db.String(100))
    location = db.Column(db.String(100))
    claimed = db.Column(db.Boolean, default=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

class FoodDatabase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    expiration_days = db.Column(db.Integer)
    cost_per_unit = db.Column(db.Float)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    category = db.Column(db.String(50))
    type = db.Column(db.String(20))
    url = db.Column(db.String(500))
