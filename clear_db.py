from app import create_app, db

app = create_app()

with app.app_context():
    # Drop all tables
    db.drop_all()
    print("All tables dropped!")
    
    # Recreate all tables
    db.create_all()
    print("All tables recreated!")
    print("Database is now empty and ready to use.")
