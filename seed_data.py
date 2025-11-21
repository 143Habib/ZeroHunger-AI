def seed_database(db, FoodDatabase, Resource):
    if FoodDatabase.query.first(): return
    
    print("Seeding database...")
    foods = [
        ("Apple", "Fruit", 14, 0.50, 95, 0.5),
        ("Banana", "Fruit", 5, 0.30, 105, 1.3),
        ("Milk", "Dairy", 7, 3.00, 150, 8.0),
        ("Chicken", "Meat", 3, 6.00, 165, 31.0),
        ("Spinach", "Vegetable", 4, 2.00, 23, 2.9),
        ("Bread", "Grain", 6, 2.50, 80, 3.0),
        ("Rice", "Grain", 365, 5.00, 200, 4.0),
        ("Eggs", "Dairy", 21, 4.00, 70, 6.0)
    ]
    for n, c, e, cost, cal, prot in foods:
        db.session.add(FoodDatabase(name=n, category=c, expiration_days=e, cost_per_unit=cost, calories=cal, protein=prot))
        
    resources = [
        ("How to Store Dairy", "Keep milk on the shelf, not the door.", "Dairy", "Article", "#"),
        ("Regrowing Veggies", "Use scraps to grow green onions.", "Vegetable", "Video", "#")
    ]
    for t, d, c, type, u in resources:
        db.session.add(Resource(title=t, description=d, category=c, type=type, url=u))
        
    db.session.commit()
    print("Database seeded!")
