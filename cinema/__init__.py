import os

import dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def create_app(test_config=None):
    app = Flask(__name__)

    dotenv.load_dotenv()
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

    db.init_app(app)

    from . import main, auth, admin, commands

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp, url_prefix="/admin")
    commands.register(app)

    return app