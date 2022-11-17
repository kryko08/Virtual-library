from crypt import methods
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for, 
    flash
)
import datetime

from .mongodb import mongo
from .forms import UserVerificationForm, BookFiltrationForm
from .auth import User

from flask_login import login_required, current_user, logout_user

import datetime
from bson.objectid import ObjectId

import pymongo


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

    def update_book(self, fields_to_update):
        query = {"_id": self._id}
        update = {"$set": fields_to_update}
        mongo.db.books.update_one(
            query,
            update
        )


@bp.route("/book-list", methods = ["GET", "POST"])
def book_list():
    form = BookFiltrationForm()
    if request.method == "POST" and form.validate():
        # Get data from form
        query = {}

        author_str = form.author_name.data
        if author_str is not None:
            query["author"] = {"$regex": f"{author_str}", "$options": "i"}

        book_str = form.book_name.data
        if book_str is not None:
            query["book_title"] = {"$regex": f"{book_str}", "$options": "i"}

        year = form.year_published.data
        if year is not None:
            year = datetime.datetime(year, 1, 1)
            query["year_published"] = year

        order = form.order_by.data # Switch Case :(
        if order:
            if order == "author":
                books = mongo.db.books.find(query).sort(str(order.split(" ")[-1]), pymongo.ASCENDING)
            else:
                books = mongo.db.books.find(query).sort(f"{order}", pymongo.ASCENDING)
        else:
            books = mongo.db.books.find(query)
        
        return render_template("app/book_list.html", form=form, books=books)
    books = mongo.db.books.find({})
    return render_template("app/book_list.html", form=form, books=books)



@bp.route("/<string:_id>/detail", methods = ["GET", "POST"])
@login_required
def book_detail(_id):
    book = mongo.db.books.find_one({"_id": ObjectId(_id)})
    user_id = current_user._id

    #borrow_check = mongo.db.users.find_one({"_id": user_id, "books": { "$elemMatch": { "book_id": _id, "to": { "$exists": False } } } })
    borrow_check = mongo.db.borrowings.find_one({"book_id": _id, "user_id": user_id})
    has_currently_borrowed = False if borrow_check is None else True

    num_currently_borrowed = mongo.db.borrowings.count_documents({"book_id": _id, "is_active": True})
    free_copies = True if num_currently_borrowed <= book["number_of_licences"] else False
  
    if request.method == "POST":

        
        if request.form["action"] == "borrow_book":
            # Borrow a book

            # Create new borrowings document
            borrowing = {
                "book_id": _id,
                "user_id": user_id,
                "is_active": True,
                "borrowed_from": datetime.now()
            }
            mongo.db.borrowings.insert_one(borrowing)

            # Add the book to the user history <----- Note

            return redirect(url_for("library.book_list"))
        
        elif request.form["action"] == "return_book":
            # Return a book
        
            # Update book record
            mongo.db.borrowings.update_one(
                {
                    "book_id": _id, 
                    "user_id": user_id,
                    "is_active": True  # User can borrow same book several times
                },
                {
                    "$set": {"is_active": True, "borrowed_to": datetime.now()}
                }
            )

        return redirect(url_for("library.book_list"))
    # method GET
    return render_template("app/book_detail.html", book=book, has_currently_borrowed=has_currently_borrowed, free_copies=free_copies)


@bp.route("/my-profile", methods = ["GET", "POST"])
@login_required
def user_books():
    # Get all books related to this user
    user_id = current_user._id 
    user = User.from_id(user_id)
    original_values = user.to_json()

    currently_borrowed = mongo.db.borrowings.find(
        {
            "user_id": user_id,
            "is_active": True
        }
        )
    previously_borrowed = mongo.db.borrowings.find(
        {
            "user_id": user_id,
            "is_active": False
        }
    )
    # Prepopulate form
    form = UserVerificationForm(obj=user)

    if request.method == "POST" and form.validate():
        # User edits their profile
        form.populate_obj(user)

        new_values = user.to_json()
        new_values["is_verified"] = False

        updated_fields = User.changed_fields(original_values, new_values)
        user.update_document(updated_fields)

        # log user out
        logout_user()
        flash(f"Změnili jste uživatelské údaje, nyní musíte čekat na schválení účtu")

        return redirect(url_for('library.book_list'))

    return render_template("app/my_account.html", currently_borrowed=currently_borrowed, previously_borrowed=previously_borrowed, form=form)
