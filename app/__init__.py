from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

# Databaseobject aanmaken (nog niet gekoppeld aan app)
db = SQLAlchemy()

def create_app():
    # Flask-app maken
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Configuratie laden (zoals DB-verbinding)
    app.config.from_object(Config)

    # Database koppelen aan de app
    db.init_app(app)

    # Routes importeren en blueprint registreren
    from app.routes import main
    app.register_blueprint(main)

    return app
