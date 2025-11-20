from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    full_name = db.Column(db.String(150))
    household_size = db.Column(db.Integer)
    dietary_pref = db.Column(db.String(100)) 
    location = db.Column(db.String(100))
    
    # NEW: Track total money spent on consumed items
    total_expenses = db.Column(db.Float, default=0.0)
    
    inventory_items = db.relationship('Inventory', backref='user', lazy=True)
    logs = db.relationship('ConsumptionLog', backref='user', lazy=True)
    uploads = db.relationship('ImageUpload', backref='user', lazy=True)

# Seeded Food Database (Reference Table)
class FoodDatabase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50)) 
    expiration_days = db.Column(db.Integer)
    
    # NEW: Default values
    cost_per_unit = db.Column(db.Float, default=0.0)
    calories = db.Column(db.Integer, default=0)
    protein = db.Column(db.Float, default=0.0)

# User Inventory
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    category = db.Column(db.String(50))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime)
    
    # NEW: Specific values for this item
    price = db.Column(db.Float, default=0.0)
    calories = db.Column(db.Integer, default=0)
    protein = db.Column(db.Float, default=0.0)

# Consumption History
class ConsumptionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    date_consumed = db.Column(db.DateTime, default=datetime.utcnow)

# Resources
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    category = db.Column(db.String(50)) 
    type = db.Column(db.String(20)) 
    url = db.Column(db.String(500)) 

# Image Uploads
class ImageUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filepath = db.Column(db.String(300))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)