from crypt import methods
from flask import (
    Blueprint,

)

from .mongodb import mongo


bp = Blueprint('library', __name__, url_prefix='')

@bp.route("/database", methods = ["GET"])
def test_mongo():
    print("TADYYYYYYYY", type(mongo.db))
    test_collection = mongo.db.testcollection.insert_one({"Funguje?" : "Ano"})
    return "<p>Hello, World!</p>"
    