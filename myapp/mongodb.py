from flask_login import LoginManager
from flask_pymongo import PyMongo

from .configmodule import MONGO_URI

mongo = PyMongo()
login_manager = LoginManager()

