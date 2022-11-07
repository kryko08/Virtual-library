from crypt import methods
from flask import (
    Blueprint,
    render_template

)

from .mongodb import mongo


bp = Blueprint('library', __name__, url_prefix='')

def get_owner_status():
    pass

@bp.route("/database", methods = ["GET"])
def test_mongo():
    print("TADYYYYYYYY", type(mongo.db))
    test_collection = mongo.db.testcollection.insert_one({"Funguje?" : "Ano"})
    return "<p>Hello, World!</p>"


@bp.route("/book-list", methods = ["GET"])
def book_list():
    return render_template("app/book_list.html")


@bp.route("/<string:_id>/detail", methods = ["GET", "POST"])
def book_detail(_id):
    return "<p>Tady bude detail knihy</p>"


@bp.route("/my-books", methods = ["GET"])
def user_books():
    return "<p>Tady budou všechny moje knihy</p>"
