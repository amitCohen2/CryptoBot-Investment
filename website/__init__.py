from flask import Flask, render_template, Blueprint
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"


# Create the Flask app
def create_app():

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'galileo'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .twitter import twitter
    from .arbitrage import arbitrage_blue_print, arbitrage_inputs

    # Register the blueprints - this is where the routes are defined
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(twitter, url_prefix='/')
    app.register_blueprint(arbitrage_blue_print, url_prefix='/')
    app.register_blueprint(arbitrage_inputs, url_prefix='/')

    from .modules import User, Note

    with app.app_context():
        db.create_all()

    # Create the login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app



