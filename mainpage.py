<<<<<<< HEAD
=======
from flask import Flask, Blueprint, render_template

# 1. Creamos la aplicación principal de Flask
app = Flask(__name__)

# 2. Tu Blueprint (si lo usas)
main = Blueprint('main', __name__)

@main.route('/')
def index():
    fake_movies = [
        {"id": 1, "title": "Inception", "genre": "Ciencia Ficción", "duration": 148, "age_rating": "12+", "poster": "inception.jpg"},
        {"id": 2, "title": "Interstellar", "genre": "Aventura / Sci-Fi", "duration": 169, "age_rating": "APTA", "poster": "interstellar.jpg"}
    ]
    return render_template('index.html', movies=fake_movies)

# 3. Registramos el Blueprint en la app
app.register_blueprint(main)

if __name__ == '__main__':
>>>>>>> 54542da06da5263cb968d04c57b8dbc17d661ae9
"""
Cinema - main Flask application.

My part (backend): routes, forms, session, glue between templates and model.

Models (SQLAlchemy, in model.py): Movie, Screen, Showtime, User (role),
Booking, FoodItem, Package, PackageItem, BookingItem, BookingPackage,
TicketPrice.
"""
import datetime
from decimal import Decimal
from functools import wraps

import sqlalchemy as sa
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

from model import (
    db,
    Movie, Screen, Showtime,
    User, UserRole,
    Booking, FoodItem, Package, TicketPrice,
)


app = Flask(__name__)
app.secret_key = "change-me-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cinema.db"
db.init_app(app)


# --------------------------------------------------------------- helpers
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please log in first.")
            return redirect(url_for("login", next=request.path))
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


def ticket_price_for(showtime):
    """Price per seat, taken from TicketPrice by day of week."""
    tp = db.session.get(TicketPrice, showtime.date.weekday())
    return tp.price if tp else Decimal("8.00")


# ---------------------------------------------------------- public pages
@app.route("/")
def index():
    movies = db.session.scalars(db.select(Movie)).all()
    return render_template("index.html", movies=movies)


@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        abort(404)
    return render_template("movie_detail.html", movie=movie)


# ----------------------------------------------------------------- auth
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email    = request.form["email"].strip().lower()
        password = request.form["password"]
        if db.session.scalar(db.select(User).where(User.email == email)):
            flash("That email is already registered.")
            return redirect(url_for("register"))
        db.session.add(User(
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole.customer,
        ))
        db.session.commit()
        flash("Account created. You can log in now.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form["email"].strip().lower()
        password = request.form["password"]
        user = db.session.scalar(db.select(User).where(User.email == email))
        if not user or not check_password_hash(user.password_hash, password):
            flash("Wrong email or password.")
            return redirect(url_for("login"))
        session["user"] = {
            "id":       user.id,
            "email":    user.email,
            "is_admin": user.role == UserRole.management_staff,
        }
        return redirect(request.args.get("next") or url_for("index"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


# -------------------------------------------------------------- booking
@app.route("/booking/<int:showtime_id>", methods=["GET", "POST"])
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
            return redirect(url_for("booking", showtime_id=showtime_id))
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
        return redirect(url_for("my_bookings"))

    return render_template(
        "booking.html",
        showtime=showtime, food=food, price_per_seat=price_per_seat,
    )


@app.route("/my_bookings")
@login_required
def my_bookings():
    bookings = db.session.scalars(
        db.select(Booking)
          .where(Booking.user_id == session["user"]["id"])
          .order_by(Booking.booking_date.desc())
    ).all()
    return render_template("my_bookings.html", bookings=bookings)


# ---------------------------------------------------------------- admin
@app.route("/manage/movies")
@admin_required
def manage_movies():
    movies = db.session.scalars(db.select(Movie)).all()
    return render_template("manage_movies.html", movies=movies)


@app.route("/manage/food")
@admin_required
def manage_food():
    food = db.session.scalars(db.select(FoodItem)).all()
    return render_template("manage_food.html", food=food)


@app.route("/manage/showtimes")
@admin_required
def manage_showtimes():
    showtimes = db.session.scalars(
        db.select(Showtime).order_by(Showtime.date, Showtime.time)
    ).all()
    return render_template("manage_showtimes.html", showtimes=showtimes)


# ------------------------------------------- bootstrap (create + seed db)
def init_db():
    """Create tables and insert demo data if empty."""
    with app.app_context():
        db.create_all()
        if db.session.scalar(db.select(sa.func.count(Movie.id))) == 0:
            seed_demo()
        db.session.commit()


def seed_demo():
    screen = Screen(name="Room 1", capacity=100)
    db.session.add(screen)
    db.session.flush()

    movies = [
        Movie(title="Dune: Part Two",
              synopsis="Paul Atreides unites with the Fremen.",
              duration=166, age_rating="PG-13", poster="", genre="Sci-fi"),
        Movie(title="Oppenheimer",
              synopsis="The making of the atomic bomb.",
              duration=180, age_rating="R", poster="", genre="Drama"),
        Movie(title="Spider-Verse",
              synopsis="Miles Morales across the multiverse.",
              duration=140, age_rating="PG", poster="", genre="Animation"),
    ]
    db.session.add_all(movies)
    db.session.flush()

    today = datetime.date.today()
    db.session.add_all([
        Showtime(movie_id=movies[0].id, screen_id=screen.id,
                 date=today, time=datetime.time(18, 0)),
        Showtime(movie_id=movies[1].id, screen_id=screen.id,
                 date=today, time=datetime.time(21, 0)),
        Showtime(movie_id=movies[2].id, screen_id=screen.id,
                 date=today + datetime.timedelta(days=1),
                 time=datetime.time(17, 0)),
    ])

    db.session.add_all([
        FoodItem(name="Popcorn (M)", description="Medium popcorn.",
                 price=Decimal("4.00")),
        FoodItem(name="Soda",        description="33 cl soft drink.",
                 price=Decimal("2.50")),
        FoodItem(name="Nachos",      description="Nachos with cheese.",
                 price=Decimal("5.00")),
    ])

    # weekday 0=Mon .. 6=Sun: cheaper on weekdays, pricier on weekends.
    for dow in range(7):
        db.session.add(TicketPrice(
            day_of_week=dow,
            price=Decimal("7.00") if dow < 5 else Decimal("9.00"),
        ))

    # one admin and one customer for testing
    db.session.add_all([
        User(email="admin@cinema.com",
             password_hash=generate_password_hash("admin"),
             role=UserRole.management_staff),
        User(email="user@cinema.com",
             password_hash=generate_password_hash("user"),
             role=UserRole.customer),
    ])


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
