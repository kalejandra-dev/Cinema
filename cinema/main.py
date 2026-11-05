from decimal import Decimal

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, abort
)

from . import db
from .model import Movie, Showtime, Booking, FoodItem, TicketPrice
from .auth import login_required

bp = Blueprint("main", __name__)


def ticket_price_for(showtime):
    """Price per seat, taken from TicketPrice by day of the week."""
    tp = db.session.get(TicketPrice, showtime.date.weekday())
    return tp.price if tp else Decimal("8.00")


# ====== Public pages ======

@bp.route("/")
def index():
    movies = db.session.scalars(db.select(Movie)).all()
    return render_template("main/index.html", movies=movies)


@bp.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        abort(404)
    return render_template("main/movie_detail.html", movie=movie)


# ====== Bookings ======

@bp.route("/booking/<int:showtime_id>", methods=["GET", "POST"])
@login_required
def booking(showtime_id):
    showtime = db.session.get(Showtime, showtime_id)
    if showtime is None:
        abort(404)

    food = db.session.scalars(
        db.select(FoodItem).where(FoodItem.available == True)  # noqa: E712
    ).all()
    price_per_seat = ticket_price_for(showtime)

    if request.method == "POST":
        num_seats = int(request.form.get("num_seats", 1))
        if num_seats < 1:
            flash("You need at least 1 seat.")
            return redirect(url_for("main.booking", showtime_id=showtime_id))

        total = price_per_seat * num_seats
        new_booking = Booking(
            user_id=session["user"]["id"],
            showtime_id=showtime.id,
            num_seats=num_seats,
            total_price=total,
        )
        db.session.add(new_booking)
        db.session.commit()
        flash("Booking confirmed.")
        return redirect(url_for("main.my_bookings"))

    return render_template("main/booking.html", showtime=showtime,
                           food=food, price_per_seat=price_per_seat)


@bp.route("/my_bookings")
@login_required
def my_bookings():
    bookings = db.session.scalars(
        db.select(Booking)
          .where(Booking.user_id == session["user"]["id"])
          .order_by(Booking.booking_date.desc())
    ).all()
    return render_template("main/my_bookings.html", bookings=bookings)