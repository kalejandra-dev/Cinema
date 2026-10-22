"""
Recreate the cinema database with demo data.

Usage (from the project folder):
    python3 seed.py

WARNING: this deletes ALL existing data (users, bookings...) and
creates the tables again with the demo data below.
"""
import datetime
from decimal import Decimal

from werkzeug.security import generate_password_hash

from mainpage import app
from model import (
    db, Movie, Screen, Showtime, User, UserRole, FoodItem, TicketPrice,
)

# Poster paths are relative to the static/ folder.
# They must match the image file names EXACTLY (including .jpg / .jpeg).
POSTERS = {
    "Dune: Part Two": "posters/dune2.jpeg",
    "Oppenheimer": "posters/oppenheimer.jpeg",
    "Spider-Verse": "posters/spider-verse.jpeg",
}


def seed():
    db.drop_all()
    db.create_all()

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

    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        seed()
    print("Database recreated with demo data.")