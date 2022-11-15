from crypt import methods
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
)
import datetime

from .mongodb import mongo

from flask_login import login_required, current_user

import datetime
from bson.objectid import ObjectId

bp = Blueprint('library', __name__, url_prefix='')

class Book():
    def __init__(self, book_title, author, number_of_pages, image_data, year_published, number_of_licenses, _id=None):
        self.book_title = book_title
        self.author = author
        self.number_of_pages = number_of_pages
        self.image_data = image_data
        self.year_published = datetime.datetime(year_published, 1, 1)
        self.number_of_licenses = number_of_licenses
        self.licences_available = number_of_licenses

        self._id = ObjectId() if _id is None else _id

    def to_json(self):
        return {
            "book_title": self.book_title,
            "author": self.author,
            "number_of_pages": self.number_of_pages,
            "image_data": self.image_data,
            "year_published": self.year_published,
            "number_of_licences": self.number_of_licenses,
            "licences_available": self.licences_available
        }

    @classmethod
    def from_id(cls, _id):
        data = mongo.db.book.find_one({"_id": ObjectId(_id)})
        if data is not None:
            return cls(**data)

    def save_to_mongo(self):
        mongo.db.books.insert_one(self.to_json())


@bp.route("/book-list", methods = ["GET"])
def book_list():
    books = mongo.db.books.find()
    return render_template("app/book_list.html", books = books)


@bp.route("/<string:_id>/detail", methods = ["GET", "POST"])
@login_required
def book_detail(_id):
    book = mongo.db.books.find_one({"_id": ObjectId(_id)})
    user_id = current_user._id

    borrow_check = mongo.db.users.find_one({"_id": user_id, "books": { "$elemMatch": { "book_id": _id, "to": { "$exists": False } } } })
    has_currently_borrowed = False if borrow_check is None else True
  
    if request.method == "POST":

        
        if request.form["action"] == "borrow_book":
            # Borrow a book

            # Decrement number of available licences
            mongo.db.books.update_one(
                {"_id": ObjectId(_id)},
                {"$inc": {"licences_available": -1}}
            )
            # Add the book to the user history
            mongo.db.users.update_one(
                {"_id": user_id},
                {"$push": {"books": {"book_id": _id, "from": datetime.datetime.now()}}}
            )
            return redirect(url_for("library.book_list"))
        
        elif request.form["action"] == "return_book":
            # Return a book
        
            # Increment number of available licences
            mongo.db.books.update_one(
                {"_id": ObjectId(_id)},
                {"$inc": {"licences_available": +1}}
            )

            # Add date of book return 
            mongo.db.users.update_one(
                {
                    "_id": user_id,
                    "books": {"$elemMatch": { "book_id": _id, "to": { "$exists": False } }}
                },
                {"$set": {"books.$.to": datetime.datetime.now()}}
            )
        return redirect(url_for("library.book_list"))
    # method GET
    return render_template("app/book_detail.html", book=book, has_currently_borrowed=has_currently_borrowed)


@bp.route("/my-books", methods = ["GET"])
def user_books():
    return 
