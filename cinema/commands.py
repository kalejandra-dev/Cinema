"""Database commands (run from the project folder with the venv active):

    flask --app=cinema init-db    # create the tables, add demo data if empty
    flask --app=cinema reset-db   # DELETE everything and recreate with demo data
"""
import datetime
from decimal import Decimal

import click
from werkzeug.security import generate_password_hash

from . import db
from .model import Movie, Screen, Showtime, User, UserRole, FoodItem, TicketPrice

# Poster paths are relative to the static/ folder.
# They must match the image file names EXACTLY (including .jpg / .jpeg).
POSTERS = {
    "Dune: Part Two": "posters/dune2.jpeg",
    "Oppenheimer": "posters/oppenheimer.jpeg",
    "Spider-Verse": "posters/spider-verse.jpeg",
}


def register(app):
    @app.cli.command("init-db")
    def init_db():
        """Create the tables and insert demo data if the db is empty."""
        db.create_all()
        if not db.session.execute(db.select(Movie)).first():
            seed_demo()
            db.session.commit()
            click.echo("Tables created with demo data.")
        else:
            click.echo("Tables already have data, nothing inserted.")

    @app.cli.command("reset-db")
    @click.confirmation_option(prompt="This deletes ALL data. Continue?")
    def reset_db():
        """Drop every table and recreate it with demo data."""
        db.drop_all()
        db.create_all()
        seed_demo()
        db.session.commit()
        click.echo("Database recreated with demo data.")


def seed_demo():
    screen = Screen(name="Room 1", capacity=100)
    db.session.add(screen)
    db.session.flush()

    movies = [
        Movie(title="Dune: Part Two",
              synopsis="Paul Atreides unites with the Fremen.",
              duration=166, age_rating="PG-13",
              poster=POSTERS["Dune: Part Two"], genre="Sci-fi"),
        Movie(title="Oppenheimer",
              synopsis="The making of the atomic bomb.",
              duration=180, age_rating="R",
              poster=POSTERS["Oppenheimer"], genre="Drama"),
        Movie(title="Spider-Verse",
              synopsis="Miles Morales across the multiverse.",
              duration=140, age_rating="PG",
              poster=POSTERS["Spider-Verse"], genre="Animation"),
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
        FoodItem(name="Soda", description="33 cl soft drink.",
                 price=Decimal("2.50")),
        FoodItem(name="Nachos", description="Nachos with cheese.",
                 price=Decimal("5.00")),
    ])

    # weekday 0=Mon .. 6=Sun: cheaper on weekdays, pricier on weekends
    for dow in range(7):
        db.session.add(TicketPrice(
            day_of_week=dow,
            price=Decimal("7.00") if dow < 5 else Decimal("9.00"),
        ))

    db.session.add_all([
        User(email="admin@cinema.com",
             password_hash=generate_password_hash("admin"),
             role=UserRole.management_staff),
        User(email="user@cinema.com",
             password_hash=generate_password_hash("user"),
             role=UserRole.customer),
    ])