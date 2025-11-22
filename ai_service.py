import os
import random
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# PASTE YOUR KEY BELOW inside the quotes
OPENAI_KEY_STRING = "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" 

client = None
try:
    from openai import OpenAI
    # Initialize the client with your specific key
    client = OpenAI(api_key=OPENAI_KEY_STRING)
except Exception as e:
    print(f"OpenAI Library not found or Key Error: {e}")
    client = None

# --- FEATURE 1: AI CONSUMPTION ANALYZER & SDG SCORE (UPDATED) ---
def analyze_patterns(user, inventory, logs):
    """
    Analyzes waste trends, nutritional balance (over/under stocking), and calculates SDG Score.
    """
    score = 50  # Base score
    insights = []
    
    # 1. WASTE ANALYSIS (Keep waste low)
    wasted_logs = [l for l in logs if l.status == 'Wasted']
    consumed_logs = [l for l in logs if l.status == 'Consumed']
    total_ops = len(wasted_logs) + len(consumed_logs)
    
    if total_ops > 0:
        waste_ratio = len(wasted_logs) / total_ops
        if waste_ratio == 0:
            score += 20
            insights.append("🏆 Perfect Streak: No food wasted recently!")
        elif waste_ratio > 0.3:
            score -= 15
            # Find most wasted category
            cat_counts = {}
            for l in wasted_logs:
                cat_counts[l.category] = cat_counts.get(l.category, 0) + 1
            if cat_counts:
                worst_cat = max(cat_counts, key=cat_counts.get)
                insights.append(f"⚠️ Waste Pattern: You frequently waste {worst_cat}. Try buying less or freezing it.")
        else:
            score += 5

    # 2. NUTRITIONAL DIVERSITY & OVER-STOCKING CHECK (New Logic)
    total_inv = len(inventory)
    if total_inv > 0:
        # Count items per category
        cat_counts = {}
        for i in inventory:
            cat_counts[i.category] = cat_counts.get(i.category, 0) + 1
        
        # Check if one category dominates (Over > 50% of inventory)
        most_stocked = max(cat_counts, key=cat_counts.get)
        dominant_ratio = cat_counts[most_stocked] / total_inv
        
        inv_cats = set(cat_counts.keys())
        
        # A. Check for Over-Stocking / Imbalance
        if dominant_ratio > 0.5 and total_inv > 3:
            score -= 5
            if most_stocked in ["Grain", "Meat"]:
                insights.append(f"⚖️ Balance Alert: Your pantry is mostly {most_stocked}. You might be lacking Vitamins found in fresh produce!")
            elif most_stocked == "Dairy":
                insights.append("🥛 Dairy Heavy: You have a lot of Dairy. Be careful, it expires quickly!")
            elif most_stocked == "Fruit":
                 insights.append("🍎 Sugar Watch: Lots of fruit! Ensure you have enough Protein/Grains for balanced energy.")
            else:
                 insights.append(f"💡 Variety Tip: You are heavily stocked on {most_stocked}. Try mixing it up for better nutrition.")
        
        # B. Check for Missing Essentials (Under-Stocking)
        elif "Vegetable" not in inv_cats and "Fruit" not in inv_cats:
            score -= 5
            insights.append("🥗 Nutrient Gap: No fresh produce detected. Consider buying Spinach or Apples for essential vitamins.")
        else:
            score += 10
            if dominant_ratio < 0.4: # Good variety
                insights.append("🌟 Great Job: Your inventory is well-balanced!")

    # 3. EXPIRATION RISK IMPACT
    risks = predict_risks(inventory)
    if len(risks) > 2:
        score -= 10
        insights.append(f"📉 Risk Alert: {len(risks)} items are about to expire. Cook them tonight!")

    # Clamp score 0-100
    return max(0, min(100, score)), insights

# --- FEATURE 4: EXPIRATION RISK PREDICTOR ---
def predict_risks(inventory):
    """
    Returns items expiring within 3 days.
    """
    now = datetime.utcnow()
    risks = []
    for item in inventory:
        if item.expiration_date:
            days = (item.expiration_date - now).days
            if days < 0:
                risks.append({'name': item.item_name, 'days': days, 'msg': "EXPIRED", 'severity': 'danger', 'id': item.id})
            elif days <= 3:
                risks.append({'name': item.item_name, 'days': days, 'msg': f"Expires in {days} days", 'severity': 'warning', 'id': item.id})
    return sorted(risks, key=lambda x: x['days'])

# --- FEATURE 2: MEAL OPTIMIZATION ENGINE ---
def generate_smart_meal_plan(inventory_obj_list, diet_pref):
    """
    Generates a plan prioritizing expiring items and dietary prefs.
    """
    # 1. Sort inventory by expiration (FIFO)
    sorted_inv = sorted(inventory_obj_list, key=lambda x: x.expiration_date if x.expiration_date else datetime.max)
    
    # 2. Categorize ingredients
    proteins = [i.item_name for i in sorted_inv if i.category in ['Meat', 'Dairy', 'Grain']]
    veggies = [i.item_name for i in sorted_inv if i.category == 'Vegetable']
    fruits = [i.item_name for i in sorted_inv if i.category == 'Fruit']
    
    # 3. AI GENERATION
    if client:
        try:
            inv_str = ", ".join([i.item_name for i in sorted_inv])
            prompt = (
                f"Create a 1-day meal plan (Breakfast, Lunch, Dinner) using these ingredients: {inv_str}. "
                f"Dietary Preference: {diet_pref}. "
                f"Prioritize using ingredients that expire soon. "
                f"Format the response as HTML using <div class='list-group'> and <a class='list-group-item'> tags. "
                f"Do not include markdown backticks."
            )
            
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a zero-waste meal planner."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"AI Error in Meal Plan: {e}")
            # Fallback continues below if AI fails

    # Fallback Logic (Mock)
    main = proteins[0] if proteins else "Beans (Pantry)"
    side = veggies[0] if veggies else "Frozen Mix"
    snack = fruits[0] if fruits else "Yogurt"
    
    return f"""
    <div class="list-group">
        <a href="#" class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between"><h5 class="mb-1">Breakfast (Offline Mode)</h5></div>
            <p class="mb-1">Oatmeal with <strong>{snack}</strong> and cinnamon.</p>
        </a>
        <a href="#" class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between"><h5 class="mb-1">Lunch</h5></div>
            <p class="mb-1"><strong>{diet_pref}</strong> Wrap with <strong>{main}</strong>.</p>
        </a>
        <a href="#" class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between"><h5 class="mb-1">Dinner</h5></div>
            <p class="mb-1">Stir-fry using <strong>{side}</strong> and <strong>{main}</strong>.</p>
        </a>
    </div>
    """

# --- FEATURE 6: NOURISHBOT (ALL ROUNDER) ---
def get_bot_response(message, inventory_list, diet):
    msg = message.lower()
    # Better formatting for empty inventory
    inv_str = ", ".join(inventory_list) if inventory_list else "currently empty"
    
    # 1. AI RESPONSE
    if client:
        try:
            # UPGRADED SYSTEM PROMPT
            system_prompt = (
                f"You are NourishBot, a delightful and expert AI Cooking Assistant & Sustainability Guide. "
                f"Your goal is to help the user eat well, save money, and reduce waste. "
                f"User's Diet: {diet}. "
                f"User's Current Inventory: {inv_str}. "
                f"INSTRUCTIONS: "
                f"1. Be friendly, encouraging, and conversational (like a master chef friend). "
                f"2. If the inventory is empty, do NOT say 'you have nothing'. Instead, ask what they are craving or suggest affordable, healthy recipes to buy ingredients for. "
                f"3. If asked about what to buy/cook, always estimate approximate costs (e.g., 'This might cost around $5'). "
                f"4. You can answer general cooking questions (e.g., 'How to chop onions') regardless of inventory. "
                f"5. Keep answers concise (under 3 sentences) unless asked for a full recipe."
            )
            
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": msg}
                ],
                max_tokens=200,
                temperature=0.8 # Slightly higher creativity for a "delightful" tone
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"AI Error in Bot: {e}")
            pass # Fall through to mock

    # 2. MOCK FALLBACK (Smarter Offline Mode)
    if "hello" in msg or "hi" in msg:
        return "Hello there! I'm NourishBot. Even though I'm in offline mode, I can still help. Are you looking for a recipe or tips on saving money?"
    elif not inventory_list and ("cook" in msg or "suggest" in msg):
        return f"Your pantry looks empty right now! For a quick budget meal, I recommend a **{diet} Stir-Fry**. You'd just need some rice, frozen veggies, and soy sauce. It costs about $3 total!"
    elif "cook" in msg or "recipe" in msg:
        return f"With {inv_str}, you could make a great skillet meal! If you need more ideas, try adding some spices like garlic or cumin."
    elif "buy" in msg or "shop" in msg:
        return "If you're shopping on a budget, look for seasonal produce and dried grains/beans—they are the cheapest way to eat healthy!"
    else:
        return "I'm here to help you cook, save money, and live sustainably. Ask me for a recipe or a shopping tip!"

# --- FEATURE 3: OCR SIMULATION ---
def mock_ocr_process():
    # Simulates scanning a receipt and finding item + weight + price
    return [
        {"name": "Milk", "cat": "Dairy", "price": 3.50, "weight": 1000, "days": 7},
        {"name": "Bananas", "cat": "Fruit", "price": 1.20, "weight": 500, "days": 4},
        {"name": "Spinach", "cat": "Vegetable", "price": 2.50, "weight": 200, "days": 3}
    ]

# --- FEATURE: BUDGET SHOPPING ---
def suggest_budget_shopping_list(budget, period, diet, current_inventory):
    """
    Generates a list of items that fit within the user's budget.
    Returns a list of dictionaries: [{'name': 'Rice', 'price': 5.0}, ...]
    """
    if not client:
        # Mock Fallback if API key is missing
        return [
            {'name': 'Bulk Rice', 'price': 5.00},
            {'name': 'Frozen Mixed Veggies', 'price': 3.50},
            {'name': 'Lentils/Beans', 'price': 2.00},
            {'name': 'Seasonal Fruit Pack', 'price': 4.00},
            {'name': 'Oats', 'price': 2.50}
        ]

    try:
        # Prompt engineering for structured output
        prompt = (
            f"Create a {period} shopping list for a {diet} diet with a strict total budget of ${budget}. "
            f"Current Pantry: {', '.join(current_inventory)}. "
            f"Focus on essentials, versatile ingredients, and nutrient density. "
            f"Output ONLY a list of items with estimated costs in this format: Item Name|Price. "
            f"Example: Milk|3.50"
        )

        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a budget meal planning expert."},
                {"role": "user", "content": prompt}
            ]
        )
        
        raw_text = resp.choices[0].message.content
        parsed_items = []
        
        # Basic parsing of the AI response
        for line in raw_text.split('\n'):
            if '|' in line:
                parts = line.split('|')
                try:
                    name = parts[0].strip().replace('- ', '').replace('• ', '')
                    price = float(parts[1].strip().replace('$', ''))
                    parsed_items.append({'name': name, 'price': price})
                except:
                    continue
        
        return parsed_items

    except Exception as e:
        print(f"AI Shopping Error: {e}")
        return []
