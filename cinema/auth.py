from functools import wraps

import flask_login
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .model import User, UserRole

bp = Blueprint("auth", __name__)


# ====== Access control for staff pages (used by admin.py) ======

def admin_required(view):
    """Like @flask_login.login_required, but the user must also be staff."""
    @wraps(view)
    @flask_login.login_required
    def wrapper(*args, **kwargs):
        if not flask_login.current_user.is_staff:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


# ====== Sign up ======

@bp.route("/register")
def register():
    return render_template("auth/register.html")


@bp.route("/register", methods=["POST"])
def register_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    query = db.select(User).where(User.email == email)
    if db.session.execute(query).scalar_one_or_none():
        flash("That email is already registered.")
        return redirect(url_for("auth.register"))

    new_user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=UserRole.customer,
    )
    db.session.add(new_user)
    db.session.commit()
    flash("Account created. You can log in now.")
    return redirect(url_for("auth.login"))


# ====== Log in / log out ======

@bp.route("/login")
def login():
    return render_template("auth/login.html")


@bp.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    query = db.select(User).where(User.email == email)
    user = db.session.execute(query).scalar_one_or_none()
    if user and check_password_hash(user.password_hash, password):
        # The user exists and the password is correct
        flask_login.login_user(user)
        # Go back to the page that asked for login, if any (only paths in this site)
        next_page = request.args.get("next", "")
        if next_page.startswith("/") and not next_page.startswith("//"):
            return redirect(next_page)
        return redirect(url_for("main.index"))

    # Wrong email and/or password
    flash("Wrong email or password.")
    return redirect(url_for("auth.login"))


@bp.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for("auth.login"))