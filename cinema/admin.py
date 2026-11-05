from flask import Blueprint, render_template

from . import db
from .model import Movie, Showtime, FoodItem
from .auth import admin_required

bp = Blueprint("admin", __name__)

# The blueprint is registered with url_prefix="/admin" in __init__.py,
# so "/movies" here is /admin/movies in the browser.


@bp.route("/movies")
@admin_required
def manage_movies():
    movies = db.session.scalars(db.select(Movie)).all()
    return render_template("admin/manage_movies.html", movies=movies)


@bp.route("/food")
@admin_required
def manage_food():
    food = db.session.scalars(db.select(FoodItem)).all()
    return render_template("admin/manage_food.html", food=food)


@bp.route("/showtimes")
@admin_required
def manage_showtimes():
    showtimes = db.session.scalars(
        db.select(Showtime).order_by(Showtime.date, Showtime.time)
    ).all()
    return render_template("admin/manage_showtimes.html", showtimes=showtimes)