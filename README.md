ZeroHunger-AI

Project Overview:
ZeroHunger-AI is a sustainable food inventory management system designed to help households reduce food waste and manage grocery expenses. The system tracks expiration dates, analyzes nutritional values, and provides sustainability resources to promote responsible food consumption.


Tech Stack

Backend:

* Python 3.x
* Flask (Web framework)
* Flask-SQLAlchemy (ORM)
* Flask-Login (Authentication and session handling)
* SQLite (Local relational database)

Frontend:

* HTML5 / Jinja2
* Bootstrap 5
* Chart.js (Data visualization)
* FontAwesome (Icons)

Project Structure

zerohunger-ai/
| app.py              - Main application and routing logic
| models.py           - Database schema and models
| seed_data.py        - Populates initial data into the database
| requirements.txt
| database.db         - Auto-created SQLite database
|
|-- templates/        - HTML templates
|-- uploads/          - Receipt images (created automatically)

Code organization follows separation of concerns:

* app.py handles routing and configuration
* models.py defines all database models
* seed_data.py loads initial food and resource data

Setup Instructions

1. Clone the Repository
   git clone <repository-url>
   cd zerohunger-ai

2. Create a Virtual Environment
   Windows:
   python -m venv venv
   venv\Scripts\activate

macOS/Linux:
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
   pip install -r requirements.txt

4. Initialize the Database
   Creates database.db and loads seed data.
   flask init-db

5. Run the Application
   python app.py
   Open in browser:
   [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

Environment Configuration Notes

* The app uses a hardcoded development secret key (innovatex_secret_key_123). For production, store it in environment variables.
* Uses SQLite (database.db) stored locally; does not require external database setup.
* The uploads/ directory is automatically created to store uploaded receipt images.

Seed Data Usage

The database includes preloaded food items with nutritional values and shelf-life durations.

How to Seed (Already linked to init):
flask init-db

How to Verify:

1. Register a new user
2. Open Inventory page
3. Search for items like "Apple" or "Milk" to auto-fill nutrition and expiration details
4. Open Resources page to view sustainability content

