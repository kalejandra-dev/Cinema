from decimal import Decimal
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, abort)
from werkzeug.security import generate_password_hash, check_password_hash

from model import (db, Movie, Showtime, User, UserRole,
                   Booking, FoodItem, TicketPrice)


app = Flask(__name__)
app.secret_key = "change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cinema.db"
db.init_app(app)


# ====== Decoradores de acceso ======

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
    tp = db.session.get(TicketPrice, showtime.date.weekday())
    return tp.price if tp else Decimal("8.00")


# ====== Páginas públicas ======

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


# ====== Autenticación ======

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if db.session.scalar(db.select(User).where(User.email == email)):
            flash("That email is already registered.")
            return redirect(url_for("register"))

        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole.customer,
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created. You can log in now.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = db.session.scalar(db.select(User).where(User.email == email))
        if not user or not check_password_hash(user.password_hash, password):
            flash("Wrong email or password.")
            return redirect(url_for("login"))

        session["user"] = {
            "id": user.id,
            "email": user.email,
            "is_admin": user.role == UserRole.management_staff,
        }
        return redirect(request.args.get("next") or url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


# ====== Reservas ======

@app.route("/booking/<int:showtime_id>", methods=["GET", "POST"])
@login_required
def booking(showtime_id):
    showtime = db.session.get(Showtime, showtime_id)
    if showtime is None:
        abort(404)

    food = db.session.scalars(
        db.select(FoodItem).where(FoodItem.available == True)
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

    return render_template("booking.html", showtime=showtime,
                           food=food, price_per_seat=price_per_seat)


@app.route("/my_bookings")
@login_required
def my_bookings():
    bookings = db.session.scalars(
        db.select(Booking)
          .where(Booking.user_id == session["user"]["id"])
          .order_by(Booking.booking_date.desc())
    ).all()
    return render_template("my_bookings.html", bookings=bookings)


# ====== Admin ======

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


# ====== Arranque ======

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
