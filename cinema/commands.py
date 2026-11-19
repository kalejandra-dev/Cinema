"""Database commands (run from the project folder with the venv active):

    flask --app=cinema init-db        # create the tables, the screens and the ticket prices
    flask --app=cinema create-admin   # create a management staff user (asks email and password)
    flask --app=cinema reset-db       # DELETE everything and run init-db again
"""
from decimal import Decimal

import click
from werkzeug.security import generate_password_hash

from . import db
from .model import Screen, TicketPrice, User, UserRole

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