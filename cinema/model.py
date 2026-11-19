# SQLAlchemy DATABASE SCRIPT
import enum
import datetime
from decimal import Decimal
from typing import Optional
import flask_login

from sqlalchemy import String, ForeignKey, Enum, Numeric, DateTime, func, UniqueConstraint, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db



class Movie(db.Model):

    __tablename__ = "movie"

    MAX_POSTER_SIZE = 2 * 1024 * 1024  # maximum poster size: 2 MiB
    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(200))

    synopsis: Mapped[str] = mapped_column(String(2000))

    duration: Mapped[int] = mapped_column()

    age_rating: Mapped[str] = mapped_column(String(20))

    poster_mime_type: Mapped[Optional[str]] = mapped_column(String(128))

    poster_data: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary(MAX_POSTER_SIZE)
    )

    genre: Mapped[str] = mapped_column(String(100))

    #I am not sure if i should keep this attribute
    showtimes: Mapped[list["Showtime"]] = relationship(
        back_populates="movie"
    )

class Screen(db.Model):

    __tablename__= "screen"

    id: Mapped[int] = mapped_column(primary_key = True)

    name: Mapped[str] = mapped_column(String(50), unique=True)

    capacity: Mapped[int] = mapped_column()

    showtimes: Mapped[list["Showtime"]] = relationship(
        back_populates="screen"
    )
    SEATS_PER_ROW = 10

    def seat_layout(self):
        """Rows of the room built from its capacity.

        Returns a list like [("A", [1, 2, ..., 10]), ("B", [1, ..., 10]), ...].
        The last row is shorter if capacity is not a multiple of SEATS_PER_ROW.
        """
        layout = []
        remaining = self.capacity
        row_index = 0
        while remaining > 0:
            seats_in_row = min(self.SEATS_PER_ROW, remaining)
            row_letter = chr(ord("A") + row_index)
            layout.append((row_letter, list(range(1, seats_in_row + 1))))
            remaining -= seats_in_row
            row_index += 1
        return layout


class Showtime(db.Model):

    __tablename__ = "showtime"

    id: Mapped[int] = mapped_column(primary_key=True)

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movie.id")
    )

    screen_id: Mapped[int] = mapped_column(
        ForeignKey("screen.id")
    )

    date: Mapped[datetime.date] = mapped_column()

    time: Mapped[datetime.time] = mapped_column()

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="showtime"
    )

    movie: Mapped["Movie"] = relationship(
        back_populates="showtimes"
    )

    screen: Mapped["Screen"] = relationship(
        back_populates="showtimes"
    )   


class UserRole(enum.Enum):
    customer = 1
    management_staff = 2

class User(flask_login.UserMixin, db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(128), unique=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255)
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole)
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user"
    )
    @property
    def is_staff(self):
        return self.role == UserRole.management_staff


class Booking(db.Model):
    __tablename__="booking"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id")
    )

    showtime_id: Mapped[int] = mapped_column(
        ForeignKey("showtime.id")
    )

    num_seats: Mapped[int] = mapped_column()

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10,2)
    )

    booking_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user: Mapped["User"] = relationship(
        back_populates = "bookings"
    )

    showtime: Mapped["Showtime"] = relationship(
        back_populates="bookings"
    )

    items: Mapped[list["BookingItem"]] = relationship(
        back_populates="booking"
    ) 

    packages: Mapped[list["BookingPackage"]] = relationship(
        back_populates="booking"
    )
    
    seats: Mapped[list["BookedSeat"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan"
    )  

class BookedSeat(db.Model):
    __tablename__ = "booked_seat"
    # The same seat cannot be booked twice for the same showtime
    __table_args__ = (
        UniqueConstraint("showtime_id", "seat_row", "seat_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id")
    )

    showtime_id: Mapped[int] = mapped_column(
        ForeignKey("showtime.id")
    )

    seat_row: Mapped[str] = mapped_column(String(2))

    seat_number: Mapped[int] = mapped_column()

    booking: Mapped["Booking"] = relationship(
        back_populates="seats"
    )

    @property
    def label(self):
        return f"{self.seat_row}{self.seat_number}"


class FoodItem(db.Model):
    __tablename__ = "food_item"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))

    description: Mapped[str] = mapped_column(String(500))

    price: Mapped[Decimal] = mapped_column(
        Numeric(10,2)
    )

    available: Mapped[bool] = mapped_column(default=True)

    package_items: Mapped[list["PackageItem"]] = relationship(
        back_populates = "food_item"
    )

    booking_items: Mapped[list["BookingItem"]] = relationship(
        back_populates="food_item"
    )


class Package(db.Model):
    
    __tablename__="package"

    id:Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))

    description: Mapped[str] = mapped_column(String(500))

    ticket_quantity: Mapped[int] = mapped_column()

    price: Mapped[Decimal] = mapped_column(
        Numeric(10,2)
    )

    available: Mapped[bool] = mapped_column(default=True)

    # delete-orphan: removing a PackageItem from package.items deletes its row
    items: Mapped[list["PackageItem"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan"
    )

    booking_packages: Mapped[list["BookingPackage"]] = relationship(
        back_populates="package"
    )

    @property
    def is_available(self):
        """It can be booked: not hidden by staff and none of its food is sold out."""
        return self.available and all(item.food_item.available for item in self.items)

    @property
    def contents(self):
        """Text like '2 tickets + 1 × Popcorn, 2 × Soda'."""
        tickets = f"{self.ticket_quantity} ticket{'s' if self.ticket_quantity != 1 else ''}"
        food = ", ".join(f"{item.quantity} × {item.food_item.name}" for item in self.items)
        return f"{tickets} + {food}" if food else tickets


class PackageItem(db.Model):

    __tablename__ = "package_item"

    package_id: Mapped[int] = mapped_column(
        ForeignKey("package.id"),
        primary_key=True
    )

    food_item_id: Mapped[int] = mapped_column(
        ForeignKey("food_item.id"),
        primary_key=True
    )

    quantity: Mapped[int] = mapped_column()

    package: Mapped["Package"] = relationship(
        back_populates="items"
    )

    food_item: Mapped["FoodItem"] = relationship(
        back_populates="package_items"
    )




class BookingItem(db.Model):
    __tablename__ = "booking_item"

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id"),
        primary_key=True
    )

    food_item_id: Mapped[int] = mapped_column(
        ForeignKey("food_item.id"),
        primary_key=True
    )

    quantity: Mapped[int] = mapped_column()

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )

    booking: Mapped["Booking"] = relationship(
        back_populates="items"
    )

    food_item: Mapped["FoodItem"] = relationship(
        back_populates="booking_items"
    )


class BookingPackage(db.Model):
    __tablename__ = "booking_package"

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id"),
        primary_key=True
    )

    package_id: Mapped[int] = mapped_column(
        ForeignKey("package.id"),
        primary_key=True
    )

    quantity: Mapped[int] = mapped_column()

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )

    booking: Mapped["Booking"] = relationship(
        back_populates="packages"
    )

    package: Mapped["Package"] = relationship(
        back_populates="booking_packages"
    )



class TicketPrice(db.Model):
    __tablename__ = "ticket_price"

    day_of_week: Mapped[int] = mapped_column(
        primary_key=True
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )

    
