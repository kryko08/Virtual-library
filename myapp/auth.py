from crypt import methods
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)

from werkzeug.security import check_password_hash, generate_password_hash

from flask_login import (
    UserMixin,
    login_user,
    login_required,
    logout_user
)
from .forms import (
    RegistrationForm,
    LoginForm,
)

from .mongodb import mongo, login_manager

from bson.objectid import ObjectId
import json

bp = Blueprint('auth', __name__, url_prefix='/auth')

login_manager.login_view = "auth.login"


# User class for session 
class User(UserMixin):
    
    def __init__(self, first_name, second_name, username, birth_number, address, password_hash, is_verified = None, banned = False, is_superuser = None, _id=None, books_borrowed=0):
        self.first_name = first_name
        self.second_name = second_name
        self.username = username

        self.birth_number = birth_number
        self.address = address

        self.password_hash = password_hash

        self.is_verified = False if is_verified is None else is_verified
        self.banned = False if banned is None else banned
        self.is_superuser = False if is_superuser is None else is_superuser

        self._id = ObjectId() if _id is None else _id
        self.books_borrowed = 0 if books_borrowed is None else books_borrowed



    def is_authenticated(self):
        return True

    def is_active(self):   
        return True           

    def is_anonymous(self):
        return False 

    def get_id(self):
        return str(self._id)

    @classmethod
    def from_id(cls, _id):
        _id = ObjectId(_id)
        data = mongo.db.users.find_one({"_id": _id})
        if data is not None:
            return cls(**data)

    @classmethod
    def from_username(cls, username):
        data = mongo.db.users.find_one({"username": username})
        if data is not None:
            return cls(**data)

    def to_json(self):
        return {
            "first_name": self.first_name,
            "second_name": self.second_name,
            "username": self.username,

            "birth_number": self.birth_number,
            "address": self.address,

            "password_hash": self.password_hash,

            "is_verified": self.is_verified,
            "banned": self.banned, 
            "is_superuser": self.is_superuser,

            "_id": self._id,
            "books_borrowed": self.books_borrowed
        } 

    def save_to_mongo(self):
        mongo.db.users.insert_one(self.to_json())

    def update_document(self, fields_to_update):
        query = {"_id": self._id}
        update = {"$set": fields_to_update}
        mongo.db.users.update_one(
            query, update
        )

    @staticmethod
    def changed_fields(old_values, new_values):
        to_update = {}
        # keys are the same
        for key in old_values.keys():
            if new_values[key] != old_values[key]:
                to_update[key] = new_values[key]
        return to_update

    def __str__(self):
        return f"Class User, {self._id}, {self.username}"

    
@bp.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    form = RegistrationForm()
    if request.method == "POST" and form.validate():
        # Get data from form
        first_name = form.first_name.data
        second_name = form.second_name.data
        username = form.username.data

        birth_number = form.birth_number.data
        address = form.address.data

        password = form.password.data
        hash_password = generate_password_hash(password)

        # Create new document
        user = User(first_name, second_name, username, birth_number, address, hash_password)
        user.save_to_mongo()

        # Redirect
        return redirect(url_for('auth.sign_up_successful'))
    return render_template('auth/signUp.html', form = form)


@bp.route("/RegistrationComplated", methods = ["GET"])
def sign_up_successful():
    return render_template('auth/signUpOK.html')


@bp.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate():
        post_username = form.username.data
        post_password = form.password.data

        # Find user with this username
        user = User.from_username(post_username)
        if type(user) is None:
            flash("Uživatelské jméno není správné")
        else:
            password = user.password_hash

            # Check password
            if check_password_hash(password, post_password):
                if not user.is_verified:
                    return redirect(url_for('auth.sign_up_successful'))

                flash("Přihlášení je úspěšné")
                # Log user in
                login_user(user)

                # Redirect to index
                return redirect(url_for('library.book_list'))

            flash("Heslo není správné")
    return render_template("auth/login.html", form = form)


@bp.route("/logout", methods = ["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('library.book_list'))


@login_manager.user_loader
def load_user(user_id):
    user = User.from_id(user_id)
    if user is not None:
        return user
    return None