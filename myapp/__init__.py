from distutils.command.config import config
import os

from flask import Flask

from . import auth
from . import library
from . import admin

from .mongodb import mongo, login_manager


def create_app(config_object = "myapp.configmodule"):
    # Create app
    app = Flask(__name__)

    #print(config_object)
    # config 
    app.config.from_object(config_object)
    
    # connect database
    mongo.init_app(app)
    # connect auth sessions
    login_manager.init_app(app)

    #print(mongo.db.testcollection.find())

    # register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(library.bp)
    app.register_blueprint(admin.bp)

    return app