import datetime
from decimal import Decimal

import flask_login
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort
)
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from . import db
from .auth import customer_required
from .model import (
    Movie, Showtime, Booking, BookedSeat, BookingItem, BookingPackage,
    FoodItem, Package, TicketPrice,
)

bp = Blueprint("main", __name__)
MAX_QUANTITY = 10       # per food item or package in a booking (max="10" in the templates)
DAYS_AHEAD = 7          # the billboard shows showtimes from now to 7 days ahead


def not_started():
    """SQL condition for showtimes that have not started yet.
    Use it inside .where(...)."""
    now = datetime.datetime.now()
    return or_(Showtime.date > now.date(),
               and_(Showtime.date == now.date(), Showtime.time > now.time()))


def upcoming():
    """SQL condition for showtimes that have not started yet and are
    at most DAYS_AHEAD days from today."""
    last_day = datetime.date.today() + datetime.timedelta(days=DAYS_AHEAD)
    return and_(not_started(), Showtime.date <= last_day)

def has_started(showtime):
    return datetime.datetime.combine(showtime.date, showtime.time) <= datetime.datetime.now()

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

def read_quantities(form, prefix, things):
    """Read the <prefix>_<id> inputs of the booking form (food_3, package_1...).

    Returns a list of (thing, quantity) with quantity > 0,
    or None if some quantity is not valid.
    """
    chosen = []
    for thing in things:
        value = form.get(f"{prefix}_{thing.id}", "") or "0"
        try:
            quantity = int(value)
        except ValueError:
            return None
        if quantity < 0 or quantity > MAX_QUANTITY:
            return None
        if quantity > 0:
            chosen.append((thing, quantity))
    return chosen


def available_packages():
    packages = db.session.scalars(db.select(Package).order_by(Package.price)).all()
    return [package for package in packages if package.is_available]


def available_food():
    return db.session.scalars(
        db.select(FoodItem).where(FoodItem.available == True)  # noqa: E712
        .order_by(FoodItem.name)
    ).all()


def check_seats(showtime, seats):
    """Return an error message, or None if all these seats can be booked."""
    if not seats:
        return "Please choose at least one seat."
    if not seats <= all_seats(showtime.screen):
        return "Some of those seats don't exist."
    already_taken = seats & taken_seats(showtime)
    if already_taken:
        return "Sorry, these seats are already taken: " + ", ".join(sorted(already_taken))
    return None


def sorted_seats(seats):
    """Seat labels in order: A1, A2, ..., A10, B1..."""
    return sorted(seats, key=lambda label: (label[0], int(label[1:])))


def showtime_started(showtime):
    flash("This showtime has already started. Please choose another one.")
    return redirect(url_for("main.movie_detail", movie_id=showtime.movie_id))

# ====== Public pages ======

@bp.route("/")
def index():
    # Movies with at least one upcoming showtime
    showing = db.select(Showtime.movie_id).where(upcoming())
    query = db.select(Movie).where(Movie.id.in_(showing)).order_by(Movie.title)
    movies = db.session.scalars(query).all()
    return render_template("main/index.html", movies=movies)


@bp.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    query = (
        db.select(Showtime)
        .where(Showtime.movie_id == movie.id)
        .where(upcoming())
        .order_by(Showtime.date, Showtime.time)
    )
    showtimes = db.session.scalars(query).all()
    return render_template("main/movie_detail.html", movie=movie, showtimes=showtimes)

@bp.route("/movie/<int:movie_id>/poster")
def movie_poster(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    if not movie.poster_data:
        abort(404, f"Movie {movie_id} does not have a poster")
    return (
        movie.poster_data,
        200,
        {"Content-Type": movie.poster_mime_type},
    )


# ====== Bookings ======

# Booking has two steps:
#   1. booking:      choose the seats (GET, the form sends them to step 2 in the URL)
#   2. booking_food: choose packages and food (GET, seats come as ?seats=C5&seats=C6)
#   confirm_booking: saves the booking (POST, seats come again in hidden fields)

@bp.route("/booking/<int:showtime_id>")
@customer_required
def booking(showtime_id):
    showtime = db.get_or_404(Showtime, showtime_id)
    if has_started(showtime):
        return showtime_started(showtime)
    # Seats already chosen, when coming back from step 2 with "Change seats"
    selected = set(request.args.getlist("seats"))
    return render_template("main/booking.html", showtime=showtime,
                           price_per_seat=ticket_price_for(showtime),
                           taken=taken_seats(showtime), selected=selected)


@bp.route("/booking/<int:showtime_id>/food")
@customer_required
def booking_food(showtime_id):
    showtime = db.get_or_404(Showtime, showtime_id)
    if has_started(showtime):
        return showtime_started(showtime)
    seats = set(request.args.getlist("seats"))
    error = check_seats(showtime, seats)
    if error:
        flash(error)
        return redirect(url_for("main.booking", showtime_id=showtime.id))
    return render_template("main/booking_food.html", showtime=showtime,
                           seats=sorted_seats(seats),
                           price_per_seat=ticket_price_for(showtime),
                           packages=available_packages(), food=available_food())


@bp.route("/booking/<int:showtime_id>/confirm", methods=["POST"])
@customer_required
def confirm_booking(showtime_id):
    showtime = db.get_or_404(Showtime, showtime_id)
    if has_started(showtime):
        return showtime_started(showtime)

    seats = set(request.form.getlist("seats"))
    error = check_seats(showtime, seats)
    if error:
        flash(error)
        return redirect(url_for("main.booking", showtime_id=showtime.id))
    back_to_food = url_for("main.booking_food", showtime_id=showtime.id,
                           seats=sorted_seats(seats))

    if "skip_food" in request.form:          # "No food, just tickets" button
        chosen_food, chosen_packages = [], []
    else:
        chosen_food = read_quantities(request.form, "food", available_food())
        chosen_packages = read_quantities(request.form, "package", available_packages())
        if chosen_food is None or chosen_packages is None:
            flash(f"Quantities must be between 0 and {MAX_QUANTITY}.")
            return redirect(back_to_food)
    # Packages include tickets: they can't include more tickets than seats chosen
    package_tickets = sum(package.ticket_quantity * quantity
                          for package, quantity in chosen_packages)
    if package_tickets > len(seats):
        flash(f"Your packages include {package_tickets} tickets, "
              f"but you chose {len(seats)} seats.")
        return redirect(back_to_food)

    price_per_seat = ticket_price_for(showtime)
    new_booking = Booking(
        user_id=flask_login.current_user.id,
        showtime_id=showtime.id,
        num_seats=len(seats),
        # seats included in packages are paid with the package price
        total_price=price_per_seat * (len(seats) - package_tickets),
    )
    for label in seats:
        new_booking.seats.append(BookedSeat(
            showtime_id=showtime.id,
            seat_row=label[0],
            seat_number=int(label[1:]),
        ))
    # Save the prices paid now, in case the menu prices change later
    for package, quantity in chosen_packages:
        new_booking.packages.append(BookingPackage(
            package_id=package.id,
            quantity=quantity,
            price=package.price,
        ))
        new_booking.total_price += package.price * quantity
    for item, quantity in chosen_food:
        new_booking.items.append(BookingItem(
            food_item_id=item.id,
            quantity=quantity,
            price=item.price,
        ))
        new_booking.total_price += item.price * quantity

    db.session.add(new_booking)
    try:
        db.session.commit()
    except IntegrityError:
        # Someone else booked one of these seats a moment ago
        db.session.rollback()
        flash("Sorry, one of those seats was just taken. Please choose again.")
        return redirect(url_for("main.booking", showtime_id=showtime.id))
    flash("Booking confirmed. Enjoy the movie!")
    return redirect(url_for("main.my_bookings"))


@bp.route("/my_bookings")
@customer_required
def my_bookings():
    mine = (
        db.select(Booking)
        .join(Booking.showtime)
        .where(Booking.user_id == flask_login.current_user.id)
    )
    # Bookings for showtimes that haven't started yet go first (shown prominently)
    upcoming_bookings = db.session.scalars(
        mine.where(not_started()).order_by(Showtime.date, Showtime.time)
    ).all()
    past_bookings = db.session.scalars(
        mine.where(~not_started()).order_by(Showtime.date.desc(), Showtime.time.desc())
    ).all()
    return render_template("main/my_bookings.html",
                           upcoming_bookings=upcoming_bookings,
                           past_bookings=past_bookings)