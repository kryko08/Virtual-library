from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from functools import wraps

from .mongodb import mongo

from flask_login import login_required, current_user

from .auth import User

from .forms import UserVerificationForm

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route("/verify", methods = ["GET", "POST"])
@login_required
def verify_list():
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
def verify_detail(_id):
    # Check admin status
    if not current_user.is_superuser:
        return abort(403)

    user = User.from_id(_id)
    form = UserVerificationForm(obj=user)

    if request.method == "POST" and form.validate():
        form.populate_obj(user)
        # Verify user
        user.is_verified = True
        user.update_document
        flash(f"Uživatel {user.username} schválen")
        return redirect(url_for('admin.verify_list'))

    return render_template('admin/user_verification.html', form = form)


@bp.route("/users")
def user_list():
    pass

@bp.route("/verify/<string:_id>/direct")
def verify_account(_id):
    pass

@bp.route("/add-new-book")
def add_book():
    pass