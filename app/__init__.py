from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # --- THE FIX: IMPORT MODELS HERE ---
    # This registers your models with SQLAlchemy before migrations run
    from app import models
    # -----------------------------------

    # Import and register Blueprints
    from app.api.main_routes import main_bp
    from app.api.admin_routes import admin_bp
    from app.api.voter_routes import voter_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voter_bp)

    return app
