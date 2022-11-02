from crypt import methods
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from .forms import RegistrationForm
from .mongodb import mongo

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route("/singUp", methods=["GET", "POST"])
def sign_up():
    form = RegistrationForm(request.POST)
    if request.method == "POST" and form.validate():
        # Get data from form
        first_name = form.first_name
        second_name = form.second_name
        username = form.user_name

        birth_number = form.birth_number
        address = form.address

        password = form.password
        hash_password = generate_password_hash(password)

        # Create new document
        mongo.db.users.insert_one(
            {
            "first_name": first_name,
            "second_name": second_name,
            "username": username,
            "birth_number": birth_number,
            "adress": address,
            "password": hash_password,
            "profile_authenticated": False,
            "is_active": True
            }
        )
        return redirect(url_for('auth.sign_up_successful'))
    else:
        form = RegistrationForm()
    return render_template('auth/signUp.html', form = form)


@bp.route("/RegistrationComplated", methods = ["GET"])
def sign_up_successful():
    return render_template('auth/signUpOK.html')


@bp.route("/login", methods = ["GET", "POST"])
def login():
    






