from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, abort
)

from . import db
from .model import Movie, Showtime, Booking, FoodItem, TicketPrice, BookedSeat
from .auth import login_required

bp = Blueprint("main", __name__)


def ticket_price_for(showtime):
    """Price per seat, taken from TicketPrice by day of the week."""
    tp = db.session.get(TicketPrice, showtime.date.weekday())
    return tp.price if tp else Decimal("8.00")

def taken_seats(showtime):
    """Labels of the seats already booked for a showtime, e.g. {"A1", "C5"}."""
    query = db.select(BookedSeat).where(BookedSeat.showtime_id == showtime.id)
    return {seat.label for seat in db.session.scalars(query)}


def all_seats(screen):
    """Labels of every seat in the room, e.g. {"A1", ..., "J10"}."""
    return {f"{row}{number}"
            for row, numbers in screen.seat_layout()
            for number in numbers}

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
        chosen = set(request.form.getlist("seats"))
        if not chosen:
            flash("Please choose at least one seat.")
            return redirect(url_for("main.booking", showtime_id=showtime_id))
        if not chosen <= all_seats(showtime.screen):
            abort(400, "Invalid seat")
        already_taken = chosen & taken_seats(showtime)
        if already_taken:
            flash("Sorry, these seats are already taken: "
                  + ", ".join(sorted(already_taken)))
            return redirect(url_for("main.booking", showtime_id=showtime_id))

        new_booking = Booking(
            user_id=session["user"]["id"],
            showtime_id=showtime.id,
            num_seats=len(chosen),
            total_price=price_per_seat * len(chosen),
        )
        for label in chosen:
            new_booking.seats.append(BookedSeat(
                showtime_id=showtime.id,
                seat_row=label[0],
                seat_number=int(label[1:]),
            ))
        db.session.add(new_booking)
        try:
            db.session.commit()
        except IntegrityError:
            # Someone else booked one of these seats a moment ago
            db.session.rollback()
            flash("Sorry, one of those seats was just taken. Please choose again.")
            return redirect(url_for("main.booking", showtime_id=showtime_id))
        flash("Booking confirmed.")
        return redirect(url_for("main.my_bookings"))

    return render_template("main/booking.html", showtime=showtime,
                           food=food, price_per_seat=price_per_seat,
                           taken=taken_seats(showtime))

@bp.route("/my_bookings")
@login_required
def my_bookings():
    bookings = db.session.scalars(
        db.select(Booking)
          .where(Booking.user_id == session["user"]["id"])
          .order_by(Booking.booking_date.desc())
    ).all()
    return render_template("main/my_bookings.html", bookings=bookings)