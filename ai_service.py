import os
import random
from datetime import datetime

# Attempt imports, handle gracefully if missing
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
except:
    client = None

# --- 1. SDG IMPACT ANALYZER ---
def analyze_impact(user, inventory, logs):
    score = 50
    insights = []
    
    # Waste Ratio
    consumed = sum(1 for l in logs if l.status == 'Consumed')
    wasted = sum(1 for l in logs if l.status == 'Wasted')
    total_logs = consumed + wasted
    
    if total_logs > 0:
        waste_ratio = wasted / total_logs
        if waste_ratio == 0:
            score += 20
            insights.append("Excellent: 0% waste recorded recently!")
        elif waste_ratio < 0.15:
            score += 10
            insights.append("Good Job: Waste is under 15%.")
        else:
            score -= 15
            insights.append("Alert: High waste detected. Freeze items before they expire.")
    
    # Expiration Check
    now = datetime.utcnow()
    expired = sum(1 for i in inventory if i.expiration_date and i.expiration_date < now)
    if expired > 0:
        score -= (expired * 5)
        insights.append(f"Action Required: {expired} items are expired.")
    else:
        score += 5

    # Diversity Bonus (SDG 2 Nutrition)
    cats = {i.category for i in inventory}
    if "Vegetable" in cats and "Fruit" in cats:
        score += 10
        insights.append("Balanced nutrition detected in inventory.")

    return max(0, min(100, score)), insights

# --- 2. RISK PREDICTION ---
def predict_risks(inventory):
    now = datetime.utcnow()
    risks = []
    for item in inventory:
        if item.expiration_date:
            days = (item.expiration_date - now).days
            if days < 0:
                risks.append({'name': item.item_name, 'msg': "EXPIRED", 'class': 'danger', 'id': item.id})
            elif days <= 3:
                risks.append({'name': item.item_name, 'msg': f"Expires in {days} days", 'class': 'warning', 'id': item.id})
    return risks

# --- 3. NOURISHBOT ---
def get_bot_response(message, inventory_list, diet):
    msg = message.lower()
    inv_str = ", ".join(inventory_list) if inventory_list else "empty pantry"

    # Use Real AI if available
    if client and os.environ.get('OPENAI_API_KEY'):
        try:
            prompt = f"Act as NourishBot, an expert in zero-waste cooking. User has: {inv_str}. Diet: {diet}. User asks: {msg}. Keep it short."
            resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role":"user", "content": prompt}])
            return resp.choices[0].message.content
        except:
            pass 
            
    # Robust Mock Logic
    if "recipe" in msg or "cook" in msg:
        return f"Try a {diet} Stir-Fry! Use {random.choice(inventory_list) if inventory_list else 'vegetables'} with garlic and soy sauce."
    elif "waste" in msg:
        return "Tip: Regrow green onions by placing the white roots in a glass of water."
    elif "hello" in msg:
        return "Hello! I'm NourishBot. Ask me how to use your leftovers."
    else:
        return f"I can help you use up your {inv_str}. Ask for a recipe!"

# --- 4. MEAL OPTIMIZER ---
def generate_meal_plan(inventory_list, diet):
    if not inventory_list:
        return "<p>Add items to inventory to get a plan!</p>"
    
    main_item = random.choice(inventory_list)
    return f"""
    <ul class="list-group">
        <li class="list-group-item"><strong>Breakfast:</strong> Smoothie with {diet} protein.</li>
        <li class="list-group-item"><strong>Lunch:</strong> Leftover {main_item} Salad.</li>
        <li class="list-group-item"><strong>Dinner:</strong> Grilled {main_item} with herbs.</li>
        <li class="list-group-item list-group-item-success"><small>Eco-Tip: This plan saves ~2kg CO2.</small></li>
    </ul>
    """

# --- 5. OCR SIMULATION ---
def mock_ocr_process():
    # Simulates extracting data from an image
    return random.sample(["Organic Milk", "Spinach", "Eggs", "Bread", "Bananas"], k=3)
