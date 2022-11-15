from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from functools import wraps

from .mongodb import mongo

from flask_login import login_required, current_user

from .auth import User
from .library import Book
from .forms import UserVerificationForm, BookCreationForm

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


@bp.route("verify/<string:_id>", methods = ["GET", "POST"])
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


@bp.route("/users", methods = ["GET"])
@login_required
def user_list():
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    user_list = mongo.db.users.find()
    return render_template("admin/user_list.html")


@bp.route("/verify/<string:_id>/direct", methods = ["GET"])
def verify_account_direct(_id):
    user = User.from_id(_id)

    new_values = {}
    new_values["is_verified"] = True
    user.update_document(new_values)
    flash(f"Uživatel {user.username} schválen")
    return render_template("admin/new_users.html")


@bp.route("/add-new-book", methods = ["GET", "POST"])
def add_book():
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
def edit_book():
    pass