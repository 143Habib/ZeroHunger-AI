import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

# Import all models including the new ShoppingItem
from models import db, User, Inventory, ConsumptionLog, FoodDatabase, Resource, SharedItem, ShoppingItem
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

# --- 1. GLOBAL CONTEXT & UTILS ---

@app.context_processor
def inject_locale():
    """Injects language dictionary into every template to fix 'txt undefined' error."""
    lang = session.get('lang', 'en')
    txt = {
        'en': {'dash': 'Dashboard', 'inv': 'Inventory', 'shop': 'Shopping List', 'com': 'Community', 'log': 'Logout'},
        'bn': {'dash': 'ড্যাশবোর্ড', 'inv': 'ইনভেন্টরি', 'shop': 'শপিং লিস্ট', 'com': 'কমিউনিটি', 'log': 'লগ আউট'}
    }
    return dict(lang=lang, txt=txt.get(lang, txt['en']))

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    session['lang'] = lang_code
    return redirect(request.referrer or url_for('dashboard'))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# --- 2. AUTHENTICATION ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form.get('email')).first():
            flash('Email taken', 'danger')
        else:
            user = User(
                email=request.form.get('email'), 
                full_name=request.form.get('name'),
                password=generate_password_hash(request.form.get('password')),
                dietary_pref=request.form.get('dietary_pref')
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- 3. DASHBOARD & ANALYTICS ---

@app.route('/')
@login_required
def dashboard():
    items = Inventory.query.filter_by(user_id=current_user.id).all()
    logs = ConsumptionLog.query.filter_by(user_id=current_user.id).order_by(ConsumptionLog.date_logged.desc()).all()
    
    # A. AI Analysis (Patterns & SDG Score)
    score, insights = ai_service.analyze_patterns(current_user, items, logs)
    current_user.sdg_score = score
    
    # B. Risk Prediction
    risks = ai_service.predict_risks(items)
    
    # C. Waste Statistics (Money & Weight)
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    weekly_logs = [l for l in logs if l.date_logged > week_ago and l.status == 'Wasted']
    
    waste_stats = {
        'money_week': sum(l.price_loss for l in weekly_logs),
        'kg_week': sum(l.weight_loss_g for l in weekly_logs) / 1000.0,
        'total_money': current_user.total_money_wasted,
        'total_kg': current_user.total_kg_wasted / 1000.0
    }
    
    db.session.commit() # Save updated score

    # D. Chart Data Preparation
    cat_data = {}
    if items:
        for i in items: cat_data[i.category] = cat_data.get(i.category, 0) + i.quantity
    else: cat_data = {'Empty': 1}

    return render_template('dashboard.html', items=items, logs=logs[:5], 
                           score=score, insights=insights, risks=risks, 
                           waste=waste_stats, cat_labels=list(cat_data.keys()), cat_data=list(cat_data.values()))

# --- 4. INVENTORY MANAGEMENT (Strict Validation) ---

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        name = request.form.get('item_name').strip()
        
        # 1. STRICT CHECK: Look for exact match (Case Insensitive)
        ref = FoodDatabase.query.filter(FoodDatabase.name.ilike(name)).first()
        
        if not ref:
            flash(f"❌ Error: '{name}' is not in our food database. Please select a valid item.", "danger")
            return redirect(url_for('inventory'))

        # 2. SUCCESS: Add to Inventory using DB Data
        new_item = Inventory(
            user_id=current_user.id, 
            item_name=ref.name, 
            category=request.form.get('category'),
            quantity=int(request.form.get('quantity')), 
            weight_g=ref.avg_weight_g or 100.0, 
            price=ref.cost_per_unit or 0.0,
            expiration_date=datetime.utcnow() + timedelta(days=ref.expiration_days or 7)
        )
        db.session.add(new_item)
        db.session.commit()
        flash(f"✅ Added {ref.name} to inventory.", "success")
        return redirect(url_for('inventory'))
        
    # GET: Fetch Inventory & ALL Valid Suggestions
    items = Inventory.query.filter_by(user_id=current_user.id).order_by(Inventory.expiration_date).all()
    all_foods = FoodDatabase.query.order_by(FoodDatabase.name).all()
    suggestions = [f.name for f in all_foods]
    
    return render_template('inventory.html', items=items, suggestions=suggestions, now=datetime.utcnow())

@app.route('/ocr_upload', methods=['POST'])
@login_required
def ocr_upload():
    if 'file' not in request.files: return redirect(url_for('inventory'))
    file = request.files['file']
    if file.filename:
        # Mock OCR Process
        detected = ai_service.mock_ocr_process()
        for d in detected:
            exp = datetime.utcnow() + timedelta(days=d['days'])
            item = Inventory(
                user_id=current_user.id, item_name=d['name'], category=d['cat'],
                quantity=1, weight_g=d['weight'], price=d['price'], expiration_date=exp
            )
            db.session.add(item)
        db.session.commit()
        flash(f"Scanned & Added: {', '.join([d['name'] for d in detected])}", "success")
    return redirect(url_for('inventory'))

@app.route('/log_action/<int:item_id>/<action>')
@login_required
def log_action(item_id, action):
    item = Inventory.query.get_or_404(item_id)
    if item.user_id != current_user.id: return redirect(url_for('dashboard'))
    
    status = "Consumed" if action == "eat" else "Wasted"
    
    # Create Log
    log = ConsumptionLog(
        user_id=current_user.id, item_name=item.item_name, category=item.category,
        status=status, price_loss=item.price, weight_loss_g=item.weight_g
    )
    db.session.add(log)
    
    # Update User Stats
    if status == "Wasted":
        current_user.total_money_wasted += item.price
        current_user.total_kg_wasted += item.weight_g
    
    # Remove from Inventory
    db.session.delete(item)
    db.session.commit()
    return redirect(request.referrer or url_for('inventory'))

# --- 5. PRO SHOPPING LIST (Budget & AI) ---

@app.route('/shopping_list', methods=['GET', 'POST'])
@login_required
def shopping_list():
    # 1. Handle Budget Settings
    if request.method == 'POST' and 'set_budget' in request.form:
        try:
            amount = float(request.form.get('budget_amount'))
            period = request.form.get('budget_period')
            current_user.budget_amount = amount
            current_user.budget_period = period
            db.session.commit()
            flash(f"Budget updated to ${amount} ({period})", "success")
        except:
            flash("Invalid budget amount.", "danger")
        return redirect(url_for('shopping_list'))

    # 2. Handle Manual Item Entry
    if request.method == 'POST' and 'add_item' in request.form:
        name = request.form.get('item_name')
        try:
            # Use input price or fallback to DB
            price_input = request.form.get('item_price')
            if price_input:
                price = float(price_input)
            else:
                ref = FoodDatabase.query.filter(FoodDatabase.name.ilike(f"%{name}%")).first()
                price = ref.cost_per_unit if ref else 0.0
            
            db.session.add(ShoppingItem(user_id=current_user.id, item_name=name, estimated_price=price))
            db.session.commit()
        except:
            flash("Error adding item.", "danger")
        return redirect(url_for('shopping_list'))

    # 3. Render Page with Calculations
    shop_items = ShoppingItem.query.filter_by(user_id=current_user.id).all()
    current_total = sum(i.estimated_price for i in shop_items)
    
    progress = 0
    if current_user.budget_amount > 0:
        progress = (current_total / current_user.budget_amount) * 100

    suggestions = [f.name for f in FoodDatabase.query.limit(50).all()]

    return render_template('shopping_list.html', 
                           items=shop_items, 
                           total=current_total, 
                           progress=progress,
                           suggestions=suggestions)

@app.route('/generate_ai_list')
@login_required
def generate_ai_list():
    if current_user.budget_amount <= 0:
        flash("Please set a budget first.", "warning")
        return redirect(url_for('shopping_list'))
        
    inv_names = [i.item_name for i in Inventory.query.filter_by(user_id=current_user.id).all()]
    
    # Call AI Service
    ai_items = ai_service.suggest_budget_shopping_list(
        current_user.budget_amount, 
        current_user.budget_period, 
        current_user.dietary_pref,
        inv_names
    )
    
    # Remove old AI items to prevent duplicates
    ShoppingItem.query.filter_by(user_id=current_user.id, added_by_ai=True).delete()
    
    # Add new AI items
    for item in ai_items:
        db.session.add(ShoppingItem(
            user_id=current_user.id, 
            item_name=item['name'], 
            estimated_price=item['price'],
            added_by_ai=True
        ))
    
    db.session.commit()
    flash("AI generated a new list based on your budget!", "success")
    return redirect(url_for('shopping_list'))

@app.route('/remove_shop_item/<int:id>')
@login_required
def remove_shop_item(id):
    item = ShoppingItem.query.get_or_404(id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('shopping_list'))

@app.route('/clear_list')
@login_required
def clear_list():
    ShoppingItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Shopping list cleared.", "info")
    return redirect(url_for('shopping_list'))

# --- 6. FEATURES: COMMUNITY, CHATBOT, RESOURCES ---

@app.route('/community', methods=['GET', 'POST'])
@login_required
def community():
    if request.method == 'POST':
        db.session.add(SharedItem(
            user_id=current_user.id,
            item_name=request.form.get('item_name'),
            description=request.form.get('description'),
            contact_info=request.form.get('contact'),
            location=current_user.location
        ))
        db.session.commit()
        flash("Item posted to community board.", "success")
        return redirect(url_for('community'))
        
    shared = SharedItem.query.filter(SharedItem.claimed==False).order_by(SharedItem.date_posted.desc()).all()
    return render_template('community.html', shared_items=shared)

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
    items = Inventory.query.filter_by(user_id=current_user.id).all()
    plan = ai_service.generate_smart_meal_plan(items, current_user.dietary_pref)
    return render_template('meal_planner.html', plan=plan)

@app.route('/articles')
@login_required
def articles():
    """New Route for Food & Sustainability Articles"""
    articles_list = Resource.query.filter_by(type="Article").all()
    return render_template('articles.html', articles=articles_list)

@app.route('/resources')
def resources():
    return render_template('resources.html', resources=Resource.query.all())

# --- 7. DATA & RUN ---

@app.route('/populate_demo')
@login_required
def populate_demo():
    """Helper to quickly load data for demonstration."""
    invs = [
        ("Milk", "Dairy", 3, 1000, 3.50), ("Spinach", "Vegetable", 2, 200, 2.00),
        ("Chicken Breast", "Meat", 4, 500, 8.00), ("Rice", "Grain", 100, 1000, 5.00)
    ]
    for n, c, d, w, p in invs:
        db.session.add(Inventory(
            user_id=current_user.id, item_name=n, category=c, 
            expiration_date=datetime.utcnow()+timedelta(days=d), weight_g=w, price=p
        ))
    db.session.commit()
    flash("Demo data loaded!", "info")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database(db, FoodDatabase, Resource)
    print("Server Running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
