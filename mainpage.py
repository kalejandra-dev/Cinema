"""
Cinema - main Flask application.

My part (backend): routes, forms, session, glue between templates and model.

Expected from model.py (friend 2, SQLAlchemy):
    - Movie, Showtime, Food, User, Booking   (classes)
    - get_movies(), get_movie(id)
    - get_showtimes(movie_id)
    - get_food_catalog()
    - create_user(name, email, password)
    - authenticate(email, password) -> User | None
    - create_booking(user_id, showtime_id, seats, food_items) -> Booking
    - get_bookings(user_id)
    - admin helpers: add_movie, edit_movie, delete_movie, same for food & showtime

While model.py is empty I use fake data so the server already runs.
"""
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, abort
)

# When friend 2 has model.py ready, swap the fake data for real queries:
# from model import (
#     get_movies, get_movie, get_showtimes, get_food_catalog,
#     create_user, authenticate, create_booking, get_bookings,
# )

app = Flask(__name__)
app.secret_key = "change-me-in-production"


# ------------------------------------------------------------------ fake data
FAKE_MOVIES = [
    {"id": 1, "title": "Dune: Part Two",   "price": 8.50, "duration": 166},
    {"id": 2, "title": "Oppenheimer",      "price": 7.00, "duration": 180},
    {"id": 3, "title": "Spider-Verse",     "price": 7.50, "duration": 140},
]
FAKE_FOOD = [
    {"id": 1, "name": "Popcorn (M)", "price": 4.00},
    {"id": 2, "name": "Soda",        "price": 2.50},
    {"id": 3, "name": "Nachos",      "price": 5.00},
]
FAKE_BOOKINGS = []  # list of {user_email, movie_id, seats, food}


# -------------------------------------------------------------------- helpers
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


# ---------------------------------------------------------------- public pages
@app.route("/")
def index():
    # movies = get_movies()
    movies = FAKE_MOVIES
    return render_template("index.html", movies=movies)


@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    # movie = get_movie(movie_id)
    movie = next((m for m in FAKE_MOVIES if m["id"] == movie_id), None)
    if movie is None:
        abort(404)
    return render_template("movie_detail.html", movie=movie)


# --------------------------------------------------------------------- auth
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form["name"]
        email    = request.form["email"]
        password = request.form["password"]
        # create_user(name, email, password)
        flash("Account created. You can log in now.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form["email"]
        password = request.form["password"]
        # user = authenticate(email, password)
        user = {"email": email, "name": email.split("@")[0], "is_admin": False}
        if not user:
            flash("Wrong email or password.")
            return redirect(url_for("login"))
        session["user"] = user
        return redirect(request.args.get("next") or url_for("index"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


# ------------------------------------------------------------------ booking
@app.route("/booking/<int:movie_id>", methods=["GET", "POST"])
@login_required
def booking(movie_id):
    movie = next((m for m in FAKE_MOVIES if m["id"] == movie_id), None)
    if movie is None:
        abort(404)
    if request.method == "POST":
        seats     = request.form.getlist("seat")
        food_ids  = request.form.getlist("food")
        # create_booking(session["user"]["id"], showtime_id, seats, food_ids)
        FAKE_BOOKINGS.append({
            "user_email": session["user"]["email"],
            "movie_id":   movie_id,
            "seats":      seats,
            "food":       food_ids,
        })
        flash("Booking confirmed.")
        return redirect(url_for("my_bookings"))
    return render_template("booking.html", movie=movie, food=FAKE_FOOD)


@app.route("/my_bookings")
@login_required
def my_bookings():
    email = session["user"]["email"]
    # bookings = get_bookings(session["user"]["id"])
    bookings = [b for b in FAKE_BOOKINGS if b["user_email"] == email]
    return render_template("my_bookings.html", bookings=bookings)


# ------------------------------------------------------------------- admin
@app.route("/manage/movies")
@admin_required
def manage_movies():
    return render_template("manage_movies.html", movies=FAKE_MOVIES)


@app.route("/manage/food")
@admin_required
def manage_food():
    return render_template("manage_food.html", food=FAKE_FOOD)


@app.route("/manage/showtimes")
@admin_required
def manage_showtimes():
    return render_template("manage_showtimes.html")


# -------------------------------------------------------------------- run
if __name__ == "__main__":
    app.run(debug=True)
