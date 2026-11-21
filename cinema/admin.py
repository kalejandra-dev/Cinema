import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, redirect, url_for, flash

from . import db
from .model import Movie, Screen, Showtime, FoodItem, Package, PackageItem
from .auth import admin_required

bp = Blueprint("admin", __name__)

# The blueprint is registered with url_prefix="/admin" in __init__.py,
# so "/movies" here is /admin/movies in the browser.


# ====== Movies ======

@bp.route("/movies")
@admin_required
def manage_movies():
    movies = db.session.scalars(db.select(Movie).order_by(Movie.title)).all()
    return render_template("admin/manage_movies.html", movies=movies)


@bp.route("/movies/new", methods=["POST"])
@admin_required
def new_movie():
    title = request.form.get("title", "").strip()
    try:
        duration = int(request.form.get("duration", ""))
    except ValueError:
        duration = 0
    if not title or duration <= 0:
        flash("A title and a valid duration are required.")
        return redirect(url_for("admin.manage_movies"))

    movie = Movie(
        title=title,
        genre=request.form.get("genre", "").strip(),
        duration=duration,
        age_rating=request.form.get("age_rating", ""),
        synopsis=request.form.get("synopsis", "").strip(),
    )

    # Optional poster, stored in the database (like the profile picture in lab 5)
    poster = request.files.get("poster")
    if poster and poster.filename:
        data = poster.read()
        if len(data) > Movie.MAX_POSTER_SIZE:
            flash("The poster is too big (max 2 MiB).")
            return redirect(url_for("admin.manage_movies"))
        if not poster.content_type.startswith("image/"):
            flash("The poster must be an image.")
            return redirect(url_for("admin.manage_movies"))
        movie.poster_data = data
        movie.poster_mime_type = poster.content_type

    db.session.add(movie)
    db.session.commit()
    flash(f"Movie '{movie.title}' added.")
    return redirect(url_for("admin.manage_movies"))


@bp.route("/movies/<int:movie_id>/delete", methods=["POST"])
@admin_required
def delete_movie(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    if movie.showtimes:
        flash(f"'{movie.title}' has showtimes. Delete them first.")
        return redirect(url_for("admin.manage_movies"))
    db.session.delete(movie)
    db.session.commit()
    flash(f"Movie '{movie.title}' deleted.")
    return redirect(url_for("admin.manage_movies"))


# ====== Showtimes ======

@bp.route("/showtimes")
@admin_required
def manage_showtimes():
    showtimes = db.session.scalars(
        db.select(Showtime).order_by(Showtime.date, Showtime.time)
    ).all()
    movies = db.session.scalars(db.select(Movie).order_by(Movie.title)).all()
    screens = db.session.scalars(db.select(Screen).order_by(Screen.name)).all()
    return render_template("admin/manage_showtimes.html",
                           showtimes=showtimes, movies=movies, screens=screens,
                           today=datetime.date.today().isoformat())


def overlapping_showtime(screen, movie, date, time):
    """Return a showtime in the same screen that overlaps with the new one, or None."""
    start = datetime.datetime.combine(date, time)
    end = start + datetime.timedelta(minutes=movie.duration)
    query = db.select(Showtime).where(Showtime.screen_id == screen.id,
                                      Showtime.date == date)
    for other in db.session.scalars(query):
        other_start = datetime.datetime.combine(other.date, other.time)
        other_end = other_start + datetime.timedelta(minutes=other.movie.duration)
        if start < other_end and other_start < end:
            return other
    return None


@bp.route("/showtimes/new", methods=["POST"])
@admin_required
def new_showtime():
    movie_id = request.form.get("movie_id", type=int)
    screen_id = request.form.get("screen_id", type=int)
    movie = db.session.get(Movie, movie_id) if movie_id else None
    screen = db.session.get(Screen, screen_id) if screen_id else None
    try:
        date = datetime.date.fromisoformat(request.form.get("date", ""))
        time = datetime.time.fromisoformat(request.form.get("time", ""))
    except ValueError:
        date = time = None
    if not movie or not screen or not date or not time:
        flash("Please choose a movie, a screen, a date and a time.")
        return redirect(url_for("admin.manage_showtimes"))
    if datetime.datetime.combine(date, time) <= datetime.datetime.now():
        flash("The showtime must be in the future.")
        return redirect(url_for("admin.manage_showtimes"))

    other = overlapping_showtime(screen, movie, date, time)
    if other:
        flash(f"{screen.name} is busy then: '{other.movie.title}' "
              f"starts at {other.time.strftime('%H:%M')}.")
        return redirect(url_for("admin.manage_showtimes"))

    db.session.add(Showtime(movie=movie, screen=screen, date=date, time=time))
    db.session.commit()
    flash(f"Showtime added: '{movie.title}' on {date.strftime('%d/%m/%Y')} "
          f"at {time.strftime('%H:%M')}.")
    return redirect(url_for("admin.manage_showtimes"))


@bp.route("/showtimes/<int:showtime_id>/delete", methods=["POST"])
@admin_required
def delete_showtime(showtime_id):
    showtime = db.get_or_404(Showtime, showtime_id)
    if showtime.bookings:
        flash("This showtime already has bookings, it can't be deleted.")
        return redirect(url_for("admin.manage_showtimes"))
    db.session.delete(showtime)
    db.session.commit()
    flash("Showtime deleted.")
    return redirect(url_for("admin.manage_showtimes"))


# ====== Food & drinks ======

@bp.route("/food")
@admin_required
def manage_food():
    food = db.session.scalars(db.select(FoodItem).order_by(FoodItem.name)).all()
    return render_template("admin/manage_food.html", food=food)

def read_food_form(form):
    """Read and check the fields of the food forms (new and edit).

    Returns (name, description, price), or None if something is not valid.
    """
    name = form.get("name", "").strip()
    try:
        price = Decimal(form.get("price", ""))
    except InvalidOperation:
        return None
    if not name or not price.is_finite() or price < 0:
        return None
    return name, form.get("description", "").strip(), price


@bp.route("/food/new", methods=["POST"])
@admin_required
def new_food():
    data = read_food_form(request.form)
    if data is None:
        flash("A name and a valid price are required.")
        return redirect(url_for("admin.manage_food"))
    name, description, price = data

    db.session.add(FoodItem(
        name=name,
        description=description,
        price=price,
        available="available" in request.form,  # unchecked checkboxes are not sent
    ))
    db.session.commit()
    flash(f"'{name}' added.")
    return redirect(url_for("admin.manage_food"))


@bp.route("/food/<int:food_id>/edit")
@admin_required
def edit_food(food_id):
    item = db.get_or_404(FoodItem, food_id)
    return render_template("admin/edit_food.html", item=item)


@bp.route("/food/<int:food_id>/edit", methods=["POST"])
@admin_required
def edit_food_post(food_id):
    item = db.get_or_404(FoodItem, food_id)
    data = read_food_form(request.form)
    if data is None:
        flash("A name and a valid price are required.")
        return redirect(url_for("admin.edit_food", food_id=item.id))

    # Bookings already made keep the price they paid (BookingItem.price)
    item.name, item.description, item.price = data
    item.available = "available" in request.form
    db.session.commit()
    flash(f"'{item.name}' updated.")
    return redirect(url_for("admin.manage_food"))


@bp.route("/food/<int:food_id>/toggle", methods=["POST"])
@admin_required
def toggle_food(food_id):
    item = db.get_or_404(FoodItem, food_id)
    item.available = not item.available
    db.session.commit()
    flash(f"'{item.name}' is now {'available' if item.available else 'sold out'}.")
    return redirect(url_for("admin.manage_food"))


@bp.route("/food/<int:food_id>/delete", methods=["POST"])
@admin_required
def delete_food(food_id):
    item = db.get_or_404(FoodItem, food_id)
    if item.booking_items or item.package_items:
        flash(f"'{item.name}' is used in bookings or packages. "
              "Mark it as sold out instead.")
        return redirect(url_for("admin.manage_food"))
    db.session.delete(item)
    db.session.commit()
    flash(f"'{item.name}' deleted.")
    return redirect(url_for("admin.manage_food"))

# ====== Packages (tickets + food, with a discount) ======

MAX_PACKAGE_TICKETS = 10
MAX_PACKAGE_ITEM_QUANTITY = 10


def read_package_form(form, food):
    """Read and check the fields of the package forms (new and edit).

    Returns (name, description, ticket_quantity, price, contents), where
    contents is a list of (FoodItem, quantity), or None if something is not valid.
    """
    name = form.get("name", "").strip()
    try:
        ticket_quantity = int(form.get("ticket_quantity", ""))
        price = Decimal(form.get("price", ""))
    except (ValueError, InvalidOperation):
        return None
    if (not name or not 1 <= ticket_quantity <= MAX_PACKAGE_TICKETS
            or not price.is_finite() or price < 0):
        return None

    contents = []
    for item in food:
        value = form.get(f"item_{item.id}", "") or "0"
        try:
            quantity = int(value)
        except ValueError:
            return None
        if not 0 <= quantity <= MAX_PACKAGE_ITEM_QUANTITY:
            return None
        if quantity > 0:
            contents.append((item, quantity))
    if not contents:
        return None  # a package must include some food or drink
    return name, form.get("description", "").strip(), ticket_quantity, price, contents


def all_food():
    return db.session.scalars(db.select(FoodItem).order_by(FoodItem.name)).all()


@bp.route("/packages")
@admin_required
def manage_packages():
    packages = db.session.scalars(db.select(Package).order_by(Package.name)).all()
    return render_template("admin/manage_packages.html",
                           packages=packages, food=all_food())


@bp.route("/packages/new", methods=["POST"])
@admin_required
def new_package():
    data = read_package_form(request.form, all_food())
    if data is None:
        flash("A name, 1 to 10 tickets, a valid price and at least one food item are required.")
        return redirect(url_for("admin.manage_packages"))
    name, description, ticket_quantity, price, contents = data

    package = Package(name=name, description=description,
                      ticket_quantity=ticket_quantity, price=price)
    for item, quantity in contents:
        package.items.append(PackageItem(food_item=item, quantity=quantity))
    db.session.add(package)
    db.session.commit()
    flash(f"Package '{name}' added.")
    return redirect(url_for("admin.manage_packages"))


@bp.route("/packages/<int:package_id>/edit")
@admin_required
def edit_package(package_id):
    package = db.get_or_404(Package, package_id)
    # Current quantity of each food item in the package, to fill in the form
    quantities = {item.food_item_id: item.quantity for item in package.items}
    return render_template("admin/edit_package.html", package=package,
                           food=all_food(), quantities=quantities)


@bp.route("/packages/<int:package_id>/edit", methods=["POST"])
@admin_required
def edit_package_post(package_id):
    package = db.get_or_404(Package, package_id)
    data = read_package_form(request.form, all_food())
    if data is None:
        flash("A name, 1 to 10 tickets, a valid price and at least one food item are required.")
        return redirect(url_for("admin.edit_package", package_id=package.id))
    package.name, package.description, package.ticket_quantity, package.price, contents = data
    package.available = "available" in request.form

    # Update the food of the package: change quantities, add new items, remove the rest
    new_quantities = {item.id: quantity for item, quantity in contents}
    for package_item in list(package.items):
        if package_item.food_item_id in new_quantities:
            package_item.quantity = new_quantities.pop(package_item.food_item_id)
        else:
            package.items.remove(package_item)   # deleted (delete-orphan)
    for item, quantity in contents:
        if item.id in new_quantities:
            package.items.append(PackageItem(food_item=item, quantity=quantity))

    db.session.commit()
    flash(f"Package '{package.name}' updated.")
    return redirect(url_for("admin.manage_packages"))


@bp.route("/packages/<int:package_id>/toggle", methods=["POST"])
@admin_required
def toggle_package(package_id):
    package = db.get_or_404(Package, package_id)
    package.available = not package.available
    db.session.commit()
    flash(f"Package '{package.name}' is now {'available' if package.available else 'hidden'}.")
    return redirect(url_for("admin.manage_packages"))


@bp.route("/packages/<int:package_id>/delete", methods=["POST"])
@admin_required
def delete_package(package_id):
    package = db.get_or_404(Package, package_id)
    if package.booking_packages:
        flash(f"'{package.name}' is used in bookings. Hide it instead.")
        return redirect(url_for("admin.manage_packages"))
    db.session.delete(package)   # its PackageItems are deleted too (cascade)
    db.session.commit()
    flash(f"Package '{package.name}' deleted.")
    return redirect(url_for("admin.manage_packages"))