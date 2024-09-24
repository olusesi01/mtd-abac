from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from user_model import User
from db import db  # Import db from the new module

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import routes after initializing db and login_manager to avoid circular import
    from routes import register_routes
    register_routes(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        #db.drop_all()
        db.create_all()

    return app
