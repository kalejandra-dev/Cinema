# SQLAlchemy DATABASE SCRIPT


import enum
import datetime
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Enum, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()



class Movie(db.Model):

    __tablename__ = "movie"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(200))

    synopsis: Mapped[str] = mapped_column(String(2000))

    duration: Mapped[int] = mapped_column()

    age_rating: Mapped[str] = mapped_column(String(20))

    poster: Mapped[str] = mapped_column(String(255))

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

class User(db.Model):
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

    items: Mapped[list["PackageItem"]] = relationship(
        back_populates="package"
    )

    booking_packages: Mapped[list["BookingPackage"]] = relationship(
        back_populates="package"
    )


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

    