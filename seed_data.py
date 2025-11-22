def seed_database(db, FoodDatabase, Resource):
    if FoodDatabase.query.first(): return
    
    print("Seeding database with food weights...")
    # Name, Category, ExpiryDays, Cost, Weight(g), Cal, Prot
    foods = [
        ("Apple", "Fruit", 14, 0.50, 150, 95, 0.5),
        ("Banana", "Fruit", 5, 0.30, 120, 105, 1.3),
        ("Milk (1L)", "Dairy", 7, 3.00, 1000, 150, 8.0),
        ("Chicken Breast", "Meat", 3, 6.00, 250, 165, 31.0),
        ("Spinach", "Vegetable", 4, 2.00, 200, 23, 2.9),
        ("Bread Loaf", "Grain", 6, 2.50, 500, 80, 3.0),
        ("Rice (1kg)", "Grain", 365, 5.00, 1000, 200, 4.0),
        ("Eggs (Dozen)", "Dairy", 21, 4.00, 600, 70, 6.0)
    ]
    resources = [
        ("10 Tips to Zero Waste Cooking", "Discover how to use every part of your vegetables, from root to stem, and save money.", "Sustainability", "Article", "https://www.healthline.com/nutrition/zero-waste-cooking"),
        ("The Ultimate Guide to Meal Prepping", "Save 5 hours a week and $200 a month by mastering the art of Sunday meal prep.", "Budgeting", "Article", "https://www.eatingwell.com/article/290678/meal-prep-101-a-beginners-guide/"),
        ("Understanding Expiration Dates", "Best-by vs Use-by? Don't throw away good food. Learn the real meaning of labels.", "Waste", "Article", "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/food-product-dating"),
        ("High Protein Vegetarian Meals", "Delicious recipes that pack a protein punch without the meat cost.", "Nutrition", "Article", "https://www.cookieandkate.com/high-protein-vegetarian-meals/"),
        ("Regrowing Veggies from Scraps", "Don't bin those green onions! Here is how to grow a garden from your kitchen waste.", "Gardening", "Article", "https://www.ruralsprout.com/regrow-vegetables/"),
        ("Smart Shopping on a Tight Budget", "Inflation hacking: How to spot deals, use coupons, and buy seasonal.", "Budgeting", "Article", "https://www.nerdwallet.com/article/finance/how-to-save-money-on-groceries")
    ]
    for t, d, c, type, u in resources:
        db.session.add(Resource(title=t, description=d, category=c, type=type, url=u))
        
    db.session.commit()
    print("Database seeded!")
    
    for n, c, e, cost, w, cal, prot in foods:
        db.session.add(FoodDatabase(name=n, category=c, expiration_days=e, cost_per_unit=cost, avg_weight_g=w, calories=cal, protein=prot))
    
    # Resources (same as before)
    db.session.add(Resource(title="Composting 101", description="Turn waste into soil.", category="Waste", type="Article", url="#"))
        
    db.session.commit()
    print("Database seeded successfully.")
