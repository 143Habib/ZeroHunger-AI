import os
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Inventory, ConsumptionLog, FoodDatabase, Resource, SharedItem
from seed_data import seed_database
import ai_service

app = Flask(__name__)
app.config['SECRET_KEY'] = 'innovatex_hackathon_key_99'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# --- LANGUAGE CONTEXT PROCESSOR ---
@app.context_processor
def inject_locale():
    lang = session.get('lang', 'en')
    txt = {
        'en': {'dash': 'Dashboard', 'inv': 'Inventory', 'shop': 'Shopping List', 'com': 'Community', 'log': 'Logout'},
        'bn': {'dash': 'ড্যাশবোর্ড', 'inv': 'ইনভেন্টরি', 'shop': 'শপিং লিস্ট', 'com': 'কমিউনিটি', 'log': 'লগ আউট'}
    }
    return dict(lang=lang, txt=txt[lang])

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    session['lang'] = lang_code
    return redirect(request.referrer or url_for('dashboard'))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# --- AUTH ROUTES ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
        else:
            user = User(
                email=email,
                full_name=request.form.get('name'),
                password=generate_password_hash(request.form.get('password')),
                dietary_pref=request.form.get('dietary_pref'),
                location=request.form.get('location')
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- MAIN FEATURES ---
@app.route('/')
@login_required
def dashboard():
    items = Inventory.query.filter_by(user_id=current_user.id).all()
    logs = ConsumptionLog.query.filter_by(user_id=current_user.id).order_by(ConsumptionLog.date_logged.desc()).all()
    
    # AI Logic
    if items or logs:
        score, insights = ai_service.analyze_impact(current_user, items, logs)
        risks = ai_service.predict_risks(items)
        current_user.sdg_score = score
        db.session.commit()
    else:
        score = 50
        insights = ["Welcome! Start logging items to see AI insights."]
        risks = []

    # Stats
    now = datetime.utcnow()
    weekly_waste = sum(l.price for l in logs if l.status == 'Wasted' and l.date_logged > now - timedelta(days=7))
    stats = {'count': len(items), 'weekly_waste': weekly_waste}

    # Chart Data
    cat_data = {}
    if items:
        for i in items:
            cat_data[i.category] = cat_data.get(i.category, 0) + i.quantity
    else:
        cat_data = {'Empty': 1}

    return render_template('dashboard.html', 
                           items=items, logs=logs[:5], 
                           score=score, insights=insights, risks=risks, stats=stats,
                           cat_labels=list(cat_data.keys()), cat_data=list(cat_data.values()))

@app.route('/populate_demo')
@login_required
def populate_demo():
    demo_items = [
        ("Organic Milk", "Dairy", 2.50, 4), 
        ("Spinach", "Vegetable", 3.00, 2), 
        ("Bread", "Grain", 4.00, 7),
        ("Chicken", "Meat", 8.00, 5)
    ]
    for n, c, p, days in demo_items:
        exp = datetime.utcnow() + timedelta(days=days)
        db.session.add(Inventory(user_id=current_user.id, item_name=n, category=c, quantity=1, price=p, expiration_date=exp))
    
    db.session.add(ConsumptionLog(user_id=current_user.id, item_name="Apple", category="Fruit", status="Consumed", price=0.5))
    db.session.add(ConsumptionLog(user_id=current_user.id, item_name="Yogurt", category="Dairy", status="Wasted", price=1.2))
    db.session.commit()
    flash("Demo Data Loaded!", "success")
    return redirect(url_for('dashboard'))

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        name = request.form.get('item_name')
        qty = int(request.form.get('quantity'))
        cat = request.form.get('category')
        
        ref = FoodDatabase.query.filter(FoodDatabase.name.ilike(f"%{name}%")).first()
        price = ref.cost_per_unit if ref else 1.0
        days = ref.expiration_days if ref else 7
        exp_date = datetime.utcnow() + timedelta(days=days)
        
        db.session.add(Inventory(
            user_id=current_user.id, item_name=name, quantity=qty, category=cat,
            expiration_date=exp_date, price=price
        ))
        db.session.commit()
        return redirect(url_for('inventory'))

    items = Inventory.query.filter_by(user_id=current_user.id).order_by(Inventory.expiration_date).all()
    suggestions = [f.name for f in FoodDatabase.query.limit(20).all()]
    return render_template('inventory.html', items=items, suggestions=suggestions, now=datetime.utcnow())

@app.route('/log_action/<int:item_id>/<action>')
@login_required
def log_action(item_id, action):
    item = Inventory.query.get_or_404(item_id)
    if item.user_id != current_user.id: return redirect(url_for('dashboard'))
    
    status = "Consumed" if action == "eat" else "Wasted"
    log = ConsumptionLog(user_id=current_user.id, item_name=item.item_name, category=item.category, status=status, price=item.price)
    db.session.add(log)
    
    if status == "Consumed":
        current_user.total_money_saved += item.price
    else:
        current_user.total_money_wasted += item.price
    
    if item.quantity > 1:
        item.quantity -= 1
    else:
        db.session.delete(item)
    
    db.session.commit()
    flash(f"Logged as {status}", "success" if status=="Consumed" else "warning")
    return redirect(request.referrer or url_for('inventory'))

@app.route('/shopping_list')
@login_required
def shopping_list():
    # Logic: Suggest items not in inventory
    staples = ["Rice", "Milk", "Eggs", "Spinach", "Bread", "Banana"]
    user_items = [i.item_name for i in Inventory.query.filter_by(user_id=current_user.id).all()]
    
    shop_list = []
    est_cost = 0.0
    
    for s in staples:
        found = False
        for ui in user_items:
            if s.lower() in ui.lower():
                found = True
                break
        if not found:
            ref = FoodDatabase.query.filter_by(name=s).first()
            price = ref.cost_per_unit if ref else 2.0
            shop_list.append({'name': s, 'reason': 'Restock Staple', 'price': price})
            est_cost += price
            
    return render_template('shopping_list.html', shop_list=shop_list, est_cost=est_cost)

@app.route('/community', methods=['GET', 'POST'])
@login_required
def community():
    if request.method == 'POST':
        # Post a new shared item
        db.session.add(SharedItem(
            user_id=current_user.id,
            item_name=request.form.get('item_name'),
            description=request.form.get('description'),
            contact_info=request.form.get('contact'),
            location=current_user.location
        ))
        db.session.commit()
        flash("Item posted for sharing!", "success")
        return redirect(url_for('community'))
        
    shared = SharedItem.query.filter(SharedItem.claimed==False).order_by(SharedItem.date_posted.desc()).all()
    return render_template('community.html', shared_items=shared)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('name')
        current_user.dietary_pref = request.form.get('dietary_pref')
        current_user.location = request.form.get('location')
        db.session.commit()
        flash('Profile updated.', 'success')
    return render_template('profile.html', user=current_user)

@app.route('/nourish_bot', methods=['GET', 'POST'])
@login_required
def nourish_bot():
    response = None
    if request.method == 'POST':
        msg = request.form.get('message')
        items = [i.item_name for i in Inventory.query.filter_by(user_id=current_user.id).all()]
        response = ai_service.get_bot_response(msg, items, current_user.dietary_pref)
    return render_template('chatbot.html', response=response)

@app.route('/meal_plan')
@login_required
def meal_plan():
    items = [i.item_name for i in Inventory.query.filter_by(user_id=current_user.id).all()]
    plan = ai_service.generate_meal_plan(items, current_user.dietary_pref)
    return render_template('meal_planner.html', plan=plan)

@app.route('/ocr_upload', methods=['POST'])
@login_required
def ocr_upload():
    if 'file' not in request.files: return redirect(url_for('inventory'))
    file = request.files['file']
    if file.filename:
        detected_items = ai_service.mock_ocr_process()
        for item_name in detected_items:
            ref = FoodDatabase.query.filter(FoodDatabase.name.ilike(f"%{item_name}%")).first()
            price = ref.cost_per_unit if ref else 1.0
            exp = datetime.utcnow() + timedelta(days=7)
            db.session.add(Inventory(
                user_id=current_user.id, item_name=item_name, quantity=1, category="Other",
                expiration_date=exp, price=price
            ))
        db.session.commit()
        flash(f"Scanned: {', '.join(detected_items)}", "info")
    return redirect(url_for('inventory'))

@app.route('/resources')
def resources():
    return render_template('resources.html', resources=Resource.query.all())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database(db, FoodDatabase, Resource)
    app.run(debug=True, port=5000)
