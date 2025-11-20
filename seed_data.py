def seed_database(db, FoodDatabase, Resource):
    if FoodDatabase.query.first():
        return

    print("Seeding Food Database with Nutrition & Prices...")

    # Format: (Name, Category, Expiration Days, Price, Calories, Protein)
    foods = [
        # --- DAIRY & EGGS ---
        ("Milk (Whole)", "Dairy", 7, 1.50, 150, 8.0),
        ("Milk (Almond)", "Dairy", 14, 2.00, 60, 1.0),
        ("Cheddar Cheese", "Dairy", 30, 5.00, 110, 7.0),
        ("Yogurt (Greek)", "Dairy", 14, 1.20, 100, 10.0),
        ("Butter", "Dairy", 90, 4.50, 100, 0.1),
        ("Eggs (Dozen)", "Protein", 21, 3.50, 70, 6.0),
        
        # --- FRUIT ---
        ("Apple", "Fruit", 21, 0.60, 95, 0.5),
        ("Banana", "Fruit", 5, 0.30, 105, 1.3),
        ("Orange", "Fruit", 14, 0.70, 45, 0.9),
        ("Avocado", "Fruit", 4, 1.50, 240, 3.0),
        ("Blueberries", "Fruit", 7, 3.50, 85, 1.1),
        
        # --- VEGETABLES ---
        ("Carrot", "Vegetable", 28, 0.20, 25, 0.6),
        ("Potato", "Vegetable", 60, 0.50, 110, 3.0),
        ("Spinach (Fresh)", "Vegetable", 5, 2.00, 23, 2.9),
        ("Broccoli", "Vegetable", 7, 1.50, 55, 3.7),
        ("Tomato", "Vegetable", 7, 0.80, 22, 1.1),

        # --- GRAINS ---
        ("Rice (White)", "Grain", 365, 2.00, 200, 4.0),
        ("Pasta (Dry)", "Grain", 365, 1.50, 200, 7.0),
        ("Bread (Slice)", "Grain", 7, 0.20, 80, 3.0),
        ("Oats", "Grain", 180, 3.00, 150, 5.0),

        # --- MEAT ---
        ("Chicken Breast", "Meat", 3, 6.00, 165, 31.0),
        ("Ground Beef", "Meat", 3, 7.00, 250, 26.0),
        ("Salmon Fillet", "Meat", 2, 9.00, 208, 20.0),
        ("Tofu", "Protein", 21, 2.50, 76, 8.0),
        
        # --- PANTRY ---
        ("Canned Beans", "Canned", 730, 1.00, 120, 7.0),
        ("Peanut Butter", "Pantry", 180, 4.00, 190, 7.0)
    ]
    
    for name, cat, exp, cost, cal, prot in foods:
        db.session.add(FoodDatabase(
            name=name, 
            category=cat, 
            expiration_days=exp, 
            cost_per_unit=cost,
            calories=cal,
            protein=prot
        ))

    # Resources remain the same
    tips = [
        ("Store Milk Correctly", "Keep milk on shelves, not the door.", "Dairy Storage", "Article", "https://www.usdairy.com"),
        ("Revive Carrots", "Soak limp carrots in ice water.", "Vegetable Hack", "Tip", "https://www.thekitchn.com"),
        ("Freeze Bread", "Slice and freeze to last months.", "Grain Storage", "Article", "https://www.lovefoodhatewaste.com"),
        ("Meal Planning 101", "Plan meals based on what expires first.", "Planning", "Guide", "https://www.choosemyplate.gov"),
        ("Understanding Expiration Dates", "Best-by vs Use-by explained.", "Education", "Video", "https://www.fsis.usda.gov")
    ]

    for t, d, c, typ, u in tips:
        db.session.add(Resource(title=t, description=d, category=c, type=typ, url=u))

    db.session.commit()
    print("Database Seeded Successfully!")