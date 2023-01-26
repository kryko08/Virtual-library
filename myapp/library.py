from crypt import methods
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for, 
    flash
)
from datetime import datetime

from .mongodb import mongo
from .forms import UserVerificationForm, BookFiltrationForm
from .auth import User

from flask_login import login_required, current_user, logout_user

from datetime import timedelta

from bson.objectid import ObjectId

import pymongo

from .utils import get_pipeline

from base64 import b64encode


bp = Blueprint('library', __name__, url_prefix='')


class Book():
    def __init__(self, book_title, author, number_of_pages, image_data, year_published, number_of_licences, licences_available, _id=None):
        self.book_title = book_title
        self.author = author
        self.number_of_pages = number_of_pages
        self.image_data = image_data
        self.year_published = year_published
        self.number_of_licences = number_of_licences
        self.licences_available = licences_available

        self._id = ObjectId() if _id is None else _id
        
    def to_json(self):
        return {
            "book_title": self.book_title,
            "author": self.author,
            "number_of_pages": self.number_of_pages,
            "image_data": self.image_data,
            "year_published": self.year_published,
            "number_of_licences": self.number_of_licences,
            "licences_available": self.licences_available, 
            "_id": self._id,
        }

    @classmethod
    def from_id(cls, _id):
        data = mongo.db.books.find_one({"_id": ObjectId(_id)})
        if data is not None:
            return cls(**data)

    def save_to_mongo(self):
        mongo.db.books.insert_one(self.to_json())

    def update_book(self, fields_to_update):
        query = {"_id": self._id}
        update = {"$set": fields_to_update}
        mongo.db.books.update_one(
            query,
            update
        )
    
    @staticmethod
    def get_user_books(user_id):
        currently_borrowed = list(mongo.db.borrowings.find(
        {
            "user_id": ObjectId(user_id),
            "is_active": True
        }
        ).sort("borrowed_from", pymongo.DESCENDING))

        currently_borrowed = None if len(currently_borrowed)==0 else currently_borrowed

        previously_borrowed = list(mongo.db.borrowings.find(
        {
            "user_id": ObjectId(user_id),
            "is_active": False
        }
        ).sort("borrowed_from", pymongo.ASCENDING))
        previously_borrowed = None if len(previously_borrowed)==0 else previously_borrowed

        return currently_borrowed, previously_borrowed


@bp.route("/book-list", methods = ["GET", "POST"])
def book_list():
    form = BookFiltrationForm()
    if request.method == "POST" and form.validate():
        # Get data from form
        search = {
            "$search": {
                "index": "BookIndex",
                "compound": {
                    "filter": []
                }
            }
        }
        pipeline = get_pipeline(form, search)
        books = mongo.db.books.aggregate(pipeline) if len(pipeline) != 0 else mongo.db.books.find({})
        return render_template("app/book_list.html", form=form, books=books)
    
    books = mongo.db.books.find({})
    return render_template("app/book_list.html", form=form, books=books)


@bp.route("/<string:_id>/detail", methods=["GET", "POST"])
@login_required
def book_detail(_id):
    book = mongo.db.books.find_one({"_id": ObjectId(_id)})
    user = current_user

    borrow_check = mongo.db.borrowings.find_one({"book_id": ObjectId(_id), "user_id": ObjectId(current_user._id), "is_active": True})
    has_currently_borrowed = False if borrow_check is None else True

    free_copies = True if book["licences_available"] > 0 else False

    allowed_books = True if user.books_borrowed < 6 else False

    # 64Base encode image
    base = b64encode(book["image_data"])
    encoding = "utf–8"
    base_string = base.decode(encoding)
    src_string = "data:image/jpeg; base64," + base_string
    book["image_data"] = src_string

    if request.method == "POST":

        if request.form["action"] == "borrow_book":
            # Borrow a book

            # Create new borrowings document
            borrowing = {
                "book_id": ObjectId(_id),
                "user_id": ObjectId(user._id),
                "is_active": True,
                "borrowed_from": datetime.now(),
                "book_title": book["book_title"]
            }
            mongo.db.borrowings.insert_one(borrowing)

            # Add the book to the user history <----- Note
            flash(f"Kniha {book['book_title']} vypůjčena")
            return redirect(url_for("library.book_list"))
        
        elif request.form["action"] == "return_book":
            # Return a book
        
            # Update book record
            mongo.db.borrowings.update_one(
                {
                    "book_id": ObjectId(_id), 
                    "user_id": ObjectId(user._id),
                    "is_active": True  # User can borrow same book several times
                },
                {
                    "$set": {"is_active": False, "borrowed_to": datetime.now()}
                }
            )
            flash(f"Kniha {book['book_title']} vrácena")
            return redirect(url_for("library.book_list"))
    # method GET
    return render_template("app/book_detail.html", book=book, has_currently_borrowed=has_currently_borrowed,
                           free_copies=free_copies, allowed_books=allowed_books)


@bp.route("/edit-my-profile", methods=["GET", "POST"])
@login_required
def edit_my_profile():
    # Get all books related to this user
    user_id = current_user._id 
    user = User.from_id(user_id)
    original_values = user.to_json()

    # Prepopulate form
    form = UserVerificationForm(obj=user)

    if request.method == "POST" and form.validate():
        # User edits their profile
        form.populate_obj(user)

        new_values = user.to_json()
        # After user details edit, user must await verification, except for superuser
        if not user.is_superuser:
            new_values["is_verified"] = False

        updated_fields = User.changed_fields(original_values, new_values)
        user.update_document(updated_fields)

        # log user out
        logout_user()
        flash(f"Změnili jste uživatelské údaje, nyní musíte čekat na schválení účtu")

        return redirect(url_for('library.book_list'))

    return render_template("app/edit_my_account.html", form=form)


@bp.route("/my-profile", methods = ["GET", "POST"])
@login_required
def my_detail():

    # Get current user 
    _id = current_user._id
    
    # Books
    books_now, books_past = Book.get_user_books(_id)
    
    if request.method == "POST":
        book_to_return_id = request.form["action"]
        # Update borrowing
        mongo.db.borrowings.update_one(
            {
                "user_id": ObjectId(_id),
                "book_id": ObjectId(book_to_return_id),
                "is_active": True
            },
            {"$set": 
                {
                    "is_active": False,
                    "borrowed_to": datetime.now()
                }
            }

        )
        flash(f"Kniha vrácena")

        return redirect(url_for("library.my_detail"))

    return render_template("app/user_detail.html", current_user=current_user,
                           books_now=books_now, books_past=books_past, d=timedelta)
    