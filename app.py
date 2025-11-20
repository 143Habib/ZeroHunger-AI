import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, FoodDatabase, Inventory, ConsumptionLog, Resource, ImageUpload
from seed_data import seed_database

app = Flask(__name__)
app.config['SECRET_KEY'] = 'innovatex_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.cli.command("init-db")
def init_db():
    db.create_all()
    seed_database(db, FoodDatabase, Resource)
    print("Database Initialized and Seeded!")

# --- AUTH ROUTES (Login/Register) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
        else:
            new_user = User(
                email=email, 
                full_name=request.form.get('name'), 
                password=generate_password_hash(password, method='pbkdf2:sha256'),
                dietary_pref=request.form.get('dietary_pref'),
                location=request.form.get('location'),
                total_expenses=0.0 # Initialize expense
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- MAIN ROUTES ---

@app.route('/')
@login_required
def dashboard():
    # 1. Get Inventory
    items = Inventory.query.filter_by(user_id=current_user.id).all()
    
    # 2. Calculate Totals for Dashboard
    inventory_count = len(items)
    total_value = sum(item.price * item.quantity for item in items)
    total_calories = sum(item.calories * item.quantity for item in items)
    total_protein = sum(item.protein * item.quantity for item in items)
    
    # 3. Chart Data
    cat_counts = {}
    for item in items:
        cat_counts[item.category] = cat_counts.get(item.category, 0) + item.quantity
        
    recent_logs = ConsumptionLog.query.filter_by(user_id=current_user.id).order_by(ConsumptionLog.date_consumed.desc()).limit(5).all()

    # 4. Recommendations
    recommendations = []
    user_categories = {item.category for item in items}
    if 'Dairy' in user_categories:
        recommendations += [(r, "Dairy Tip") for r in Resource.query.filter_by(category='Dairy Storage').all()]
    if len(recommendations) < 3:
        recommendations += [(r, "General Tip") for r in Resource.query.filter_by(category='Waste Reduction').limit(3).all()]

    return render_template('dashboard.html', 
                           count=inventory_count, 
                           total_value=round(total_value, 2),
                           total_calories=total_calories,
                           total_protein=round(total_protein, 1),
                           logs=recent_logs, 
                           recommendations=recommendations[:3],
                           cat_labels=list(cat_counts.keys()),
                           cat_data=list(cat_counts.values()),
                           now=datetime.utcnow())

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        name = request.form.get('item_name')
        qty = int(request.form.get('quantity'))
        cat = request.form.get('category')
        
        # Look up item in Seed Database for Auto-fill
        ref_item = FoodDatabase.query.filter(FoodDatabase.name.ilike(f"{name}")).first()
        
        exp_date = None
        price = 0.0
        calories = 0
        protein = 0.0
        
        if ref_item:
            # Auto-Calculate Expiry
            exp_date = datetime.utcnow() + timedelta(days=ref_item.expiration_days)
            if cat == 'Other': cat = ref_item.category
            # Auto-Fill Metrics
            price = ref_item.cost_per_unit
            calories = ref_item.calories
            protein = ref_item.protein
        
        new_item = Inventory(
            user_id=current_user.id, 
            item_name=name, 
            quantity=qty, 
            category=cat, 
            expiration_date=exp_date,
            price=price,
            calories=calories,
            protein=protein
        )
        db.session.add(new_item)
        db.session.commit()
        flash(f'{name} added! Value: ${price}, Cal: {calories}', 'success')
        return redirect(url_for('inventory'))
        
    items = Inventory.query.filter_by(user_id=current_user.id).order_by(Inventory.expiration_date.asc()).all()
    suggested_foods = [f.name for f in FoodDatabase.query.with_entities(FoodDatabase.name).all()]
    
    return render_template('inventory.html', items=items, suggested_foods=suggested_foods, now=datetime.utcnow())

@app.route('/log_consumption', methods=['POST'])
@login_required
def log_consumption():
    name = request.form.get('item_name')
    cat = request.form.get('category')
    
    inv_item = Inventory.query.filter_by(user_id=current_user.id, item_name=name).first()
    if inv_item:
        # EXPENSE TRACKING LOGIC
        # Add the price of 1 unit to the user's total expenses
        if inv_item.price:
            current_user.total_expenses += inv_item.price
            
        # Update Quantity
        if inv_item.quantity > 1:
            inv_item.quantity -= 1
        else:
            db.session.delete(inv_item)
            
        # Log
        db.session.add(ConsumptionLog(user_id=current_user.id, item_name=name, category=cat))
        db.session.commit()
        flash(f'Consumed {name}. ${inv_item.price} added to profile expenses.', 'success')
        
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files: return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '': return redirect(url_for('dashboard'))
    if file:
        if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        db.session.add(ImageUpload(user_id=current_user.id, filepath=filepath))
        db.session.commit()
        flash('Receipt uploaded!', 'info')
        return redirect(url_for('dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('name')
        current_user.dietary_pref = request.form.get('dietary_pref')
        current_user.location = request.form.get('location')
        db.session.commit()
        flash('Profile Updated', 'success')
    return render_template('profile.html')

@app.route('/resources')
@login_required
def resources():
    return render_template('resources.html', resources=Resource.query.all())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database(db, FoodDatabase, Resource)
    app.run(debug=True)