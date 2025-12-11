from flask import Flask
from flask_migrate import Migrate      
from .models import db
from .config import Config

migrate = Migrate()                    

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Load blueprints (shared main object and all domain modules)
    from .blueprints import main  # noqa: F401
    from . import routes  # noqa: F401

    app.register_blueprint(main)

    return app
