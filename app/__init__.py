from flask import Flask
from flask_migrate import Migrate      
from .models import db
from .config import Config

migrate = Migrate()                    

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)         # MIGRATE KOPPELEN AAN APP + DB

    # DIT NIET MEER GEBRUIKEN:
    # with app.app_context():
    #     db.create_all()  # Create sql tables for our data models

    from .routes import main
    app.register_blueprint(main)

    return app