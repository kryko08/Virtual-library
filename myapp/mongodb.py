from flask_login import LoginManager
from flask_pymongo import PyMongo

from .configmodule import MONGO_URI
import json
from bson.objectid import ObjectId

mongo = PyMongo()
login_manager = LoginManager()


class MyJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return ObjectId.toString()
        return json.JSONEncoder.default(self, o)

