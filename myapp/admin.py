from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort, send_file
)
from functools import wraps

from .mongodb import mongo
import pymongo

from flask_login import login_required, current_user

from .auth import User
from .library import Book
from .forms import UserVerificationForm, BookCreationForm, BookEditForm, UserFiltrationForm, DatabaseImportForm

from datetime import datetime, timedelta

from PIL import Image
from io import BytesIO
import base64

import subprocess
import shlex

from .configmodule import MONGO_URI

import os

import re
from mmap import ACCESS_READ, mmap

bp = Blueprint('admin', __name__, url_prefix='/admin')


# User Verification Views
@bp.route("/verify", methods = ["GET", "POST"])
@login_required
def user_verify_list():
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    waiting_list = mongo.db.users.find(
        {
            "$and": [{"is_verified": False}, {"banned": False}]
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

        if request.form["action"] == "verify":
            form.populate_obj(user)
            
            new_values = user.to_json()
            new_values["is_verified"] = True

            updated_fields = User.changed_fields(original_values, new_values)
            user.update_document(updated_fields)

            flash(f"Uživatel {user.username} schválen")
            return redirect(url_for('admin.user_verify_list'))
        
        elif request.form["action"] == "ban":
            user.update_document({"banned": True})
            flash(f"Uživatel {user.username} zabanován")
            return redirect(url_for('admin.user_verify_list'))
        
    return render_template('admin/user_verification.html', form = form)


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


# User list   
@bp.route("/users", methods = ["GET", "POST"])
@login_required
def user_list():
    form = UserFiltrationForm()
    if request.method == "POST" and form.validate():
        # Get data from form
        pipeline = []
        search = {
            "$search": {
                "index": "UserIndex",
                "compound": {
                    "filter": []
                }
            }
        }
        # Check for text input
        for field_name, value in list(form.data.items())[:-2]:
            if value != "":
                regex_pattern = f".*{value}.*"
                regex_params = {
                    "path": field_name,
                    "query": regex_pattern,
                    "allowAnalyzedField": True
                }
                regex_dict = {}
                regex_dict["regex"] = regex_params
                search["$search"]["compound"]["filter"].append(regex_dict)

        pipeline.append(search) if len(search["$search"]["compound"]["filter"]) != 0 else 0 # Append nothing

        # Check for sort 
        order = form.order_by.data
        if order:
            sort = {
                "$sort": {
                    order: -1
                }
            }
            pipeline.append(sort)
        
        users = mongo.db.users.aggregate(pipeline) if len(pipeline) != 0 else mongo.db.users.find({})
        return render_template("admin/user_list.html", form=form, users=users)
    
    users = mongo.db.users.find({})
    return render_template("admin/user_list.html", form=form, users=users)

# User detail
@bp.route("/users/<string:_id>/detail", methods = ["GET", "POST"])
@login_required
def user_detail(_id):
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)
    
    user = mongo.db.users.find_one({"_id": _id})

    # Books
    books_now, books_past = Book.get_user_books(_id)
    
    if request.method == "POST":
        book_to_return_id = request.form["action"]
        # Update borrowing
        mongo.db.borrowings.update_one(
            {
                "user_id": _id,
                "book_id": book_to_return_id,
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
        # Get updated data
        books_now, books_past = Book.get_user_books(_id)
        return redirect(url_for("admin.user_detail", user=user, books_now=books_now, books_past=books_past, d=timedelta))

    return render_template("admin/user_detail.html", current_user=current_user, books_now=books_now, books_past=books_past, d=timedelta)
 
   
# Book Manipulation Views 
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

    

    book = Book.from_id(_id)
    original_values = book.to_json()

    form = BookEditForm(obj=book)

    if request.method == "POST" and form.validate():
        form.populate_obj(book)
         
        new_values = book.to_json()

        updated_fields = User.changed_fields(original_values, new_values)
        book.update_document(updated_fields)

        return redirect(url_for('library.book_list'))

    return render_template('admin/edit_book.html', form = form, currently_borrowed_by=currently_borrowed_by)

class MongoExport():

    def __init__(self, uri):
        self.uri = uri

    def get_command(self, collection):
        command = f"mongodump --uri {self.uri} --collection {collection} --archive"
        return command
    
    def execute(self, command):
        cmd = shlex.split(command)
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        return out, err

        
@bp.route("/export-mongo", methods = ["GET", "POST"])
@login_required
def export_mongo():
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    export = MongoExport(MONGO_URI)
    if request.method == "POST":
        file_path = os.path.join(os.getcwd(), "export.netstring")
        collections = ["test_collection", "borrowings", "books", "users"]

        # Get blocks 
        blocks = []
        for collection_name in collections:
            print(collection_name)
            cmd = export.get_command(collection_name)
            stream, error = export.execute(cmd)
            blocks.append(stream)
        
        # Save to .txt file
        with open(file_path, 'wb') as file:
            for blob in blocks:
                # [len]":"[string]","
                file.write(str(len(blob)).encode())
                file.write(b":")
                file.write(blob)
                file.write(b",")
                
        return send_file(file_path, as_attachment=True)
                
        
    return render_template("admin/export.html")

class MongoImport():

    def __init__(self, uri):
        self.uri = uri
    
    def get_command(self, collection):
        # collection_with_ext = os.path.split(collection_from_bson)[-1]
        # collection = os.path.splitext(collection_with_ext)[0]
        command = f"mongorestore --uri {self.uri} --collection {collection} --archive --drop"
        return command

    def execute(self, command, iostream):
        cmd = shlex.split(command)
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate(input=iostream)
        print("OUT", out)
        print("ERROR", err)
        print("\n")


@bp.route("/import-mongo", methods = ["GET", "POST"])
@login_required
def import_mongo():
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)
    
    form = DatabaseImportForm()

    if request.method == "POST":
        # Handle file
        file = request.files["import_file"]
        file_path = os.path.join(os.getcwd(), "export.netstring")
        file.save(file_path)

        blocks = []
        match_size = re.compile(br'(\d+):').match
        with open(file_path, 'rb') as file, mmap(file.fileno(), 0, access=ACCESS_READ) as mm:
            position = 0
            for m in iter(lambda: match_size(mm, position), None):
                i, size = m.end(), int(m.group(1))
                blocks.append(mm[i:i + size])
                position = i + size + 1 # shift to the next netstring

        # import obj
        import_mongo = MongoImport(MONGO_URI)
        collections = ["test_collection", "borrowings", "books", "users"]
        for (blob, collection) in zip(blocks, collections):
            cmd = import_mongo.get_command(collection)
            import_mongo.execute(cmd, blob)

    # Remove file
    # os.remove(file_path) 
    return render_template("admin/import.html", form=form)
    

    
    