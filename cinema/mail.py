"""Booking confirmation emails.

The SMTP server is configured in .env (see README). If MAIL_SERVER is not set,
the email is printed in the terminal instead of being sent, so the app also
works without an email account (useful for local development).
"""
import smtplib
from email.message import EmailMessage

from flask import current_app


def booking_email_text(booking):
    """Plain text body with the details of a booking."""
    showtime = booking.showtime
    seats = ", ".join(sorted((seat.label for seat in booking.seats),
                             key=lambda label: (label[0], int(label[1:]))))
    lines = [
        "Thank you for your booking!",
        "",
        f"Movie:   {showtime.movie.title}",
        f"Date:    {showtime.date.strftime('%A %d/%m/%Y')}",
        f"Time:    {showtime.time.strftime('%H:%M')}",
        f"Screen:  {showtime.screen.name}",
        f"Seats:   {seats}",
    ]
    if booking.packages:
        lines.append("")
        lines.append("Packages:")
        for item in booking.packages:
            lines.append(f"  {item.quantity} x {item.package.name} "
                         f"({item.price * item.quantity:.2f} EUR)")
    if booking.items:
        lines.append("")
        lines.append("Food & drinks:")
        for item in booking.items:
            lines.append(f"  {item.quantity} x {item.food_item.name} "
                         f"({item.price * item.quantity:.2f} EUR)")
    lines += [
        "",
        f"Total:   {booking.total_price:.2f} EUR",
        "",
        "Enjoy the movie!",
    ]
    return "\n".join(lines)


def send_booking_confirmation(booking):
    """Send the confirmation email of a booking to its user.

    Returns True if the email was sent, False if it failed, and None if
    no email server is configured (the email is only printed in the terminal).
    A failure must not cancel the booking, so errors are only logged.
    """
    config = current_app.config
    message = EmailMessage()
    message["Subject"] = f"Booking confirmed: {booking.showtime.movie.title}"
    message["From"] = config.get("MAIL_SENDER") or config.get("MAIL_USERNAME") or "cinema@localhost"
    message["To"] = booking.user.email
    message.set_content(booking_email_text(booking))

    if not config.get("MAIL_SERVER"):
        # No email server configured: show the email in the terminal
        print("=" * 60)
        print(message)
        print("=" * 60)
        current_app.logger.warning("MAIL_SERVER is not set in .env: the booking email was not sent")
        return None

    try:
        # local_hostname: by default smtplib sends the computer name, and Gmail
        # rejects it (error 501) when it has non-ASCII characters (e.g. Chinese)
        with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"],
                          local_hostname="localhost", timeout=10) as smtp:
            smtp.starttls()
            if config.get("MAIL_USERNAME"):
                smtp.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
            smtp.send_message(message)
        return True
    except (smtplib.SMTPException, OSError):
        current_app.logger.exception("Could not send the booking email")
        return False
