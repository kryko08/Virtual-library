from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from functools import wraps

from .mongodb import mongo
import pymongo

from flask_login import login_required, current_user

from .auth import User
from .library import Book
from .forms import UserVerificationForm, BookCreationForm, BookEditForm, UserFiltrationForm

from datetime import date

from PIL import Image
from io import BytesIO
import base64

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route("/verify", methods = ["GET", "POST"])
@login_required
def user_verify_list():
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    waiting_list = mongo.db.users.find(
        {
            "is_verified": False
        }
    )
    return render_template('admin/new_users.html', waiting_list=waiting_list)


@bp.route("users/verify/<string:_id>", methods = ["GET", "POST"])
@login_required
def user_verify_detail(_id):
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    user = User.from_id(_id)
    original_values = user.to_json()

    form = UserVerificationForm(obj=user)

    if request.method == "POST" and form.validate():
        form.populate_obj(user)
         
        new_values = user.to_json()
        new_values["is_verified"] = True

        updated_fields = User.changed_fields(original_values, new_values)
        user.update_document(updated_fields)

        flash(f"Uživatel {user.username} schválen")
        return redirect(url_for('admin.user_verify_list'))

    return render_template('admin/user_verification.html', form = form)


@bp.route("/users", methods = ["GET", "POST"])
@login_required
def user_list():
    form = UserFiltrationForm()
    if request.method == "POST" and form.validate():
        # Get data from form
        query = {}

        first_name = form.first_name.data
        if first_name is not None:
            query["first_name"] = {"$regex": f"{first_name}", "$options": "i"}

        second_name = form.second_name.data
        if second_name is not None:
            query["second_name"] = {"$regex": f"{second_name}", "$options": "i"}

        address = form.address.data
        if address is not None:
            query["address"] = {"$regex": f"{address}", "$options": "i"}

        birth_number = form.birth_number.data
        if birth_number is not None:
            query["birth_number"] = {"$regex": f"{birth_number}", "$options": "i"}

        order = form.order_by.data 
        if order:
            users = mongo.db.users.find(query).sort(f"{order}", pymongo.ASCENDING)
        else:
            users = mongo.db.users.find(query)
        return render_template("admin/user_list.html", form=form, users=users)

    users = mongo.db.users.find({})
    return render_template("admin/user_list.html", form=form, users=users)



@bp.route("users/verify/<string:_id>/direct", methods = ["GET"])
@login_required
def verify_account_direct(_id):
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    user = User.from_id(_id)

    new_values = {}
    new_values["is_verified"] = True
    user.update_document(new_values)
    flash(f"Uživatel {user.username} schválen")
    return render_template("admin/new_users.html")


@bp.route("/add-new-book", methods = ["GET", "POST"])
@login_required
def add_book():
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    form = BookCreationForm()
    if request.method == "POST" and form.validate():
        # Get data from form
        book_title = form.book_title.data
        author = form.author.data
        number_of_pages = form.number_of_pages.data

        file = request.files['title_page']
        image = Image.open(file)
        im_bytes = BytesIO()
        image.save(im_bytes, format='PNG')
        base = base64.b64encode(im_bytes.getvalue())

        year_published = form.year_published.data
        
        number_of_licences = form.number_of_licences.data

        book = Book(book_title, author, number_of_pages, base, year_published, number_of_licences)
        book.save_to_mongo()

        # Redirect
        return redirect(url_for('library.book_list'))
    return render_template('admin/add_book.html', form = form)


@bp.route("/<string:_id>/edit", methods = ["GET", "POST"])
@login_required
def edit_book(_id):
     # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    # Book can not be edited if the book si currently borrowed
    currently_borrowed_by = mongo.db.borrowings.find(
        {
        "book_id": _id,
        "is_active": True
        },
        {
        "user_id": 1,
        "book_id": 0 
        }
    )

    book = Book.from_id(_id)
    original_values = book.to_json()

    form = BookEditForm(obj=book)

    if request.method == "POST" and form.validate():
        form.populate_obj(book)
         
        new_values = book.to_json()
        new_values["is_verified"] = True

        updated_fields = User.changed_fields(original_values, new_values)
        book.update_document(updated_fields)

        return redirect(url_for('library.book_list'))

    return render_template('admin/edit_book.html', form = form, currently_borrowed_by=currently_borrowed_by)


# Přehodit do library, upravit přístupy
@bp.route("/users/<string:_id>/detail", methods = ["GET", "POST"])
def user_detail(_id):
    user = mongo.db.users.find_one({"_id": _id})
    # list all books borrowed currently
    books_now = mongo.db.borrowings.find(
        {
            "user_id": _id,
            "is_active": True
        }
    )
    books_past = mongo.db.borrowings.find(
        {
            "user_id": _id,
            "is_active": False
        }
    )
    if request.method == "POST":
        redirect(url_for("admin.user_detail", _id=_id))
    render_template("admin/user_detail.html", user=user, books_now=books_now, books_past=books_past)
    