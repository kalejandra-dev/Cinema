"""Database commands (run from the project folder with the venv active):

    flask --app=cinema init-db        # create the tables, the screens and the ticket prices
    flask --app=cinema create-admin   # create a management staff user (asks email and password)
    flask --app=cinema reset-db       # DELETE everything and run init-db again
    flask --app=cinema seed-demo      # add the snacks menu, demo movies, showtimes and a customer
    flask --app=cinema seed-demo --menu-only   # add only the snacks menu (food, combos, deals)
"""
import datetime
import mimetypes
import os
from decimal import Decimal

import click
from werkzeug.security import generate_password_hash

from . import db
from .model import (
    Screen, TicketPrice, User, UserRole, Movie, Showtime,
    FoodItem, FoodCategory, Package, PackageItem,
)

# The cinema has 6 screens with 100 seats each (10 rows of 10, see Screen.seat_layout)
SCREENS = [(f"Screen {number}", 100) for number in range(1, 7)]

# Ticket price per day of the week: 0 = Monday ... 6 = Sunday
TICKET_PRICES = {
    0: Decimal("7.00"),   # Monday
    1: Decimal("7.00"),   # Tuesday
    2: Decimal("5.00"),   # Wednesday: "día del espectador"
    3: Decimal("7.00"),   # Thursday
    4: Decimal("7.00"),   # Friday
    5: Decimal("11.00"),  # Saturday
    6: Decimal("11.00"),  # Sunday
}


def create_basic_data():
    """Create the screens and set the ticket prices.

    It can be run more than once: it only adds the screens that are missing
    and updates the prices to the values above.
    """
    for name, capacity in SCREENS:
        query = db.select(Screen).where(Screen.name == name)
        if db.session.execute(query).scalar_one_or_none() is None:
            db.session.add(Screen(name=name, capacity=capacity))

    for day, price in TICKET_PRICES.items():
        ticket_price = db.session.get(TicketPrice, day)
        if ticket_price is None:
            db.session.add(TicketPrice(day_of_week=day, price=price))
        else:
            ticket_price.price = price

    db.session.commit()


def register(app):
    @app.cli.command("init-db")
    def init_db():
        """Create the tables, the screens and the ticket prices."""
        db.create_all()
        create_basic_data()
        click.echo("Database ready: tables, screens and ticket prices.")

    @app.cli.command("reset-db")
    @click.confirmation_option(prompt="This deletes ALL data (movies, users, bookings...). Continue?")
    def reset_db():
        """Drop every table and create everything again (empty)."""
        db.drop_all()
        db.create_all()
        create_basic_data()
        click.echo("Database recreated: tables, screens and ticket prices.")

    register_seed(app)

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(email, password):
        """Create a management staff user."""
        email = email.strip().lower()
        query = db.select(User).where(User.email == email)
        if db.session.execute(query).scalar_one_or_none():
            raise click.ClickException(f"{email} is already registered.")
        db.session.add(User(
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole.management_staff,
        ))
        db.session.commit()
        click.echo(f"Admin {email} created.")


# ====== Demo data (seed-demo) ======

# Food: (category, name, detail, price, image in static/snacks/)
# Names "Group - Size" are shown together in the menu (see FoodItem.group and .label).
# Only the first item of each group needs the image: the menu uses it for the whole group.
DEMO_FOOD = [
    (FoodCategory.drinks, "Drink - Small", "750 ml", "2.50", "drink.jpg"),
    (FoodCategory.drinks, "Drink - Medium", "1 L", "3.50", None),
    (FoodCategory.drinks, "Drink - Large", "1.25 L", "4.50", None),
    (FoodCategory.popcorn, "Popcorn - Small", "Small bucket", "3.00", "popcorn.png"),
    (FoodCategory.popcorn, "Popcorn - Medium", "Medium bucket", "4.00", None),
    (FoodCategory.popcorn, "Popcorn - Large", "Large bucket", "5.00", None),
    (FoodCategory.nachos, "Nachos - Plain", "No sauce", "2.00", "nachos.jpg"),
    (FoodCategory.nachos, "Nachos - 1 Sauce", "Salsa or cheese", "2.50", None),
    (FoodCategory.nachos, "Nachos - 2 Sauces", "Salsa and cheese", "3.00", None),
    (FoodCategory.hot_dogs, "Hot Dog - Classic", "One hot dog", "1.50", "hotdog.jpg"),
    (FoodCategory.sweets, "Snickers", "", "1.00", "snickers.png"),
    (FoodCategory.sweets, "Twix", "", "1.00", "twix.jpg"),
    (FoodCategory.sweets, "Filipinos", "", "2.00", "filipinos.jpg"),
    (FoodCategory.sweets, "Milka", "", "2.00", "milka.jpg"),
    (FoodCategory.sweets, "Haribo", "", "2.50", "haribo.jpg"),
]

# Packages: (name, tickets, price, image, [(food name, quantity), ...])
# 0 tickets = combo (only food, cheaper together). 1 or more = deal (price includes the tickets).
DEMO_PACKAGES = [
    ("Popcorn Combo - Small", 0, "5.00", "popcombo.png",
     [("Popcorn - Small", 1), ("Drink - Small", 1)]),
    ("Popcorn Combo - Medium", 0, "7.00", None,
     [("Popcorn - Medium", 1), ("Drink - Medium", 1)]),
    ("Popcorn Combo - Large", 0, "9.00", None,
     [("Popcorn - Large", 1), ("Drink - Large", 1)]),
    ("Nachos Combo", 0, "6.00", "nachocombo.png",
     [("Nachos - 2 Sauces", 1), ("Drink - Medium", 1)]),
    ("Hot Dog Combo", 0, "4.00", "hotcombo.png",
     [("Hot Dog - Classic", 1), ("Drink - Medium", 1)]),
    ("Duo Deal", 2, "22.00", "Duo.png",
     [("Popcorn - Large", 1), ("Drink - Medium", 2), ("Snickers", 2)]),
    ("Family Deal", 4, "49.00", "family.png",
     [("Popcorn - Large", 2), ("Drink - Medium", 4), ("Haribo", 2), ("Snickers", 2)]),
]

# Movies: (title, genre, minutes, age rating, synopsis, poster in static/posters/, days until release)
DEMO_MOVIES = [
    ("Dune: Part Two", "Sci-fi", 166, "PG-13",
     "Paul Atreides unites with Chani and the Fremen while seeking revenge "
     "against the conspirators who destroyed his family.", "dune2.jpeg", None),
    ("Oppenheimer", "Drama", 180, "R",
     "The story of American scientist J. Robert Oppenheimer and his role "
     "in the development of the atomic bomb.", "oppenheimer.jpeg", None),
    ("Spider-Verse", "Animation", 140, "PG",
     "Miles Morales catapults across the Multiverse, where he meets a team "
     "of Spider-People charged with protecting its very existence.", "spider-verse.jpeg", None),
    ("Dune: Part Three", "Sci-fi", 165, "PG-13",
     "The next chapter of the Dune saga.", None, 30),
]

# Movies that the previous version of the app showed as "Coming soon" (by title)
OLD_COMING_SOON = {"Avengers: Doomsday": datetime.date(2026, 12, 18),
                   "Dune: Part Three": datetime.date(2026, 12, 18)}


def static_image(app, folder, filename):
    """Read an image from cinema/static/<folder>/. Returns (data, mime_type)."""
    path = os.path.join(app.static_folder, folder, filename)
    with open(path, "rb") as file:
        return file.read(), mimetypes.guess_type(path)[0]


def find(model, **filters):
    return db.session.execute(db.select(model).filter_by(**filters)).scalar_one_or_none()


def seed_menu(app):
    """Add the snacks menu. Existing items (same name) keep their price,
    they only get the category, detail and image they don't have yet."""
    added = completed = 0
    for category, name, detail, price, image in DEMO_FOOD:
        item = find(FoodItem, name=name)
        if item is None:
            item = FoodItem(name=name, description="", category=category,
                            detail=detail, price=Decimal(price), available=True)
            db.session.add(item)
            added += 1
        else:
            if item.category in (None, FoodCategory.other):
                item.category = category
            if not item.detail:
                item.detail = detail
            completed += 1
        if image and not item.image_data:
            item.image_data, item.image_mime_type = static_image(app, "snacks", image)
    db.session.flush()

    for name, tickets, price, image, contents in DEMO_PACKAGES:
        package = find(Package, name=name)
        if package is None:
            # Look for the food first, before adding new objects to the session
            food = [(find(FoodItem, name=food_name), quantity) for food_name, quantity in contents]
            package = Package(name=name, description="", ticket_quantity=tickets,
                              price=Decimal(price), available=True)
            db.session.add(package)
            for food_item, quantity in food:
                package.items.append(PackageItem(food_item=food_item, quantity=quantity))
            added += 1
        else:
            completed += 1
            if package.ticket_quantity != tickets:
                click.echo(f"  Check '{name}': it includes {package.ticket_quantity} ticket(s) "
                           f"(demo: {tickets}) and costs {package.price} €.")
        if image and not package.image_data:
            package.image_data, package.image_mime_type = static_image(app, "snacks", image)
    click.echo(f"Snacks menu: {added} added, {completed} already existed.")


def seed_movies(app):
    """Add demo movies with posters, and showtimes for the next days."""
    today = datetime.date.today()
    screens = db.session.scalars(db.select(Screen).order_by(Screen.id)).all()
    for i, (title, genre, minutes, rating, synopsis, poster, days) in enumerate(DEMO_MOVIES):
        if find(Movie, title=title):
            continue
        movie = Movie(title=title, genre=genre, duration=minutes, age_rating=rating,
                      synopsis=synopsis)
        if poster:
            movie.poster_data, movie.poster_mime_type = static_image(app, "posters", poster)
        first_day = today + datetime.timedelta(days=1)
        if days:
            movie.release_date = today + datetime.timedelta(days=days)
            first_day = movie.release_date
        db.session.add(movie)
        # Two showtimes a day for 3 days, each movie in its own screen
        for day in range(3):
            for hour in (17, 21):
                db.session.add(Showtime(movie=movie, screen=screens[i % len(screens)],
                                        date=first_day + datetime.timedelta(days=day),
                                        time=datetime.time(hour, 0)))
        click.echo(f"Movie added: {title}")

    if not find(User, email="user@cinema.com"):
        db.session.add(User(email="user@cinema.com",
                            password_hash=generate_password_hash("user"),
                            role=UserRole.customer))
        click.echo("Customer added: user@cinema.com / user")


def update_old_data():
    """Data from the previous version of the app: coming soon movies were chosen by title."""
    for title, release_date in OLD_COMING_SOON.items():
        movie = find(Movie, title=title)
        if movie and movie.release_date is None:
            movie.release_date = release_date
            click.echo(f"Release date of '{title}' set to {release_date}.")


def register_seed(app):
    @app.cli.command("seed-demo")
    @click.option("--menu-only", is_flag=True, help="Only the snacks menu (food, combos, deals).")
    def seed_demo(menu_only):
        """Add demo data. It only adds what is missing, so it can be run more than once."""
        db.create_all()
        create_basic_data()
        update_old_data()
        seed_menu(app)
        if not menu_only:
            seed_movies(app)
        db.session.commit()
        click.echo("Done.")
