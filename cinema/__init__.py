import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
	pass

db = SQLAlchemy(model_class=Base)

def create_app():
	app = Flask(__name__)
	
	app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")

	db.init_app(app)

	from . import model

	return app


