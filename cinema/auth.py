from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .model import User, UserRole

bp = Blueprint("auth", __name__)


# ====== Access decorators (used by main.py and admin.py) ======

def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please log in first.")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user or not user.get("is_admin"):
            abort(403)
        return view(*args, **kwargs)
    return wrapper


# ====== Authentication ======

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if db.session.scalar(db.select(User).where(User.email == email)):
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

    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = db.session.scalar(db.select(User).where(User.email == email))
        if not user or not check_password_hash(user.password_hash, password):
            flash("Wrong email or password.")
            return redirect(url_for("auth.login"))

        session["user"] = {
            "id": user.id,
            "email": user.email,
            "is_admin": user.role == UserRole.management_staff,
        }
        return redirect(request.args.get("next") or url_for("main.index"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("main.index"))