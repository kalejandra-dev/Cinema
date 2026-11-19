# Cinema
Web application for a movie theater with multiple screens. Users can browse movies that are currently showing or will be shown in the next few days, view details of each movie, and book tickets for a specific screening. They can also include popcorn and drinks in their booking. Managing staff add movies and showtimes, and edit the food and beverage items available for sale in the theater.

- Contributors: Alejandra, Haoqi and Martin.

## Features

- **Billboard**: movies with at least one showtime in the next 7 days.
- **Movie detail**: synopsis, poster and upcoming showtimes.
- **Booking**: seat map (taken seats are disabled), food and drinks, live total price.
  Ticket price depends on the day: Mon, Tue, Thu, Fri 7 €; Wednesday ("día del espectador") 5 €; Sat, Sun 11 €.
- **My bookings**: seats, food and total of each booking.
- **Staff pages**: add / delete movies (with poster upload), showtimes (no overlaps in the same screen) and food items (mark as sold out).
- Following the labs: app factory + blueprints, Flask-SQLAlchemy, **Flask-Login** for sessions,
  **CSRF protection** with Flask-WTF, posters stored in the database and served by a route.

## Project structure

The project follows the same layout as the lab application (microblog):
an application factory (`create_app`) plus one blueprint per area.

```
Cinema/                      <- project folder (repository)
├── .env                     # SECRET_KEY, SQLALCHEMY_DATABASE_URI (NOT committed)
├── .gitignore
├── requirements.txt
├── README.md
├── coordination.txt
├── instance/                # local SQLite database, created by Flask (NOT committed)
└── cinema/                  <- Python package with the app
    ├── __init__.py          # create_app(), db, LoginManager, CSRFProtect
    ├── model.py             # SQLAlchemy models (Movie, Screen, Showtime, User, Booking...)
    ├── main.py              # blueprint "main": billboard, movie detail, poster, booking, my bookings
    ├── auth.py              # blueprint "auth": register, login, logout + admin_required
    ├── admin.py             # blueprint "admin": manage movies, showtimes, food
    ├── commands.py          # flask init-db / create-admin / reset-db
    ├── static/
    │   ├── style.css
    │   ├── bg_page.jpeg
    │   └── seat_map.js      # seat selection and live totals on the booking page
    └── templates/
        ├── base.html        # common layout, every page extends it
        ├── _poster.html     # partial: movie poster or placeholder
        ├── main/            # index, movie_detail, booking, my_bookings
        ├── auth/            # login, register
        └── admin/           # manage_movies, manage_showtimes, manage_food
```

## Setup (once per computer)

1. Create and activate a virtual environment, then install the dependencies:

   macOS / Linux:
   ```
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```

   Windows:
   ```
   py -3 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   Activate the virtual environment again every time you open a new terminal.

2. Create a `.env` file in the project folder (next to `requirements.txt`).

   Local development (SQLite):
   ```
   SECRET_KEY=put-something-long-and-random-here
   SQLALCHEMY_DATABASE_URI=sqlite:///cinema.db
   ```

   Lab MariaDB (only works from the lab computers or https://aulavirtual.lab.it.uc3m.es/):
   ```
   SECRET_KEY=put-something-long-and-random-here
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://27_webapp_XX:PASSWORD@mysql.lab.it.uc3m.es/27_webapp_XXa
   ```
   If the password contains `@`, `:`, `/` or `#`, write them as `%40`, `%3A`, `%2F`, `%23`.

   Each person creates their own `.env`. It is in `.gitignore`, never commit it.

3. Create the tables, the 6 screens and the ticket prices:
   ```
   flask --app=cinema init-db
   ```

4. Create a staff user (it asks for an email and a password):
   ```
   flask --app=cinema create-admin
   ```
   Customers sign up from the web (`/register`). Users created there are always customers.

## Running the app

```
flask --debug --app=cinema run
```

Open http://127.0.0.1:5000 in the browser and log in with the staff user to add
movies, showtimes and food from the "Manage" pages. Stop the server with Ctrl + C.

If `flask` gives `No module named 'dotenv'` (or another missing module) although the
virtual environment is active, use `python -m flask ...` instead of `flask ...`.

## Database commands

| Command                            | What it does                                                        |
|------------------------------------|---------------------------------------------------------------------|
| `flask --app=cinema init-db`       | Creates missing tables, the 6 screens and the ticket prices. Safe to run again. |
| `flask --app=cinema create-admin`  | Creates a staff user (asks for email and password)                  |
| `flask --app=cinema reset-db`      | DELETES all data and recreates the tables, screens and prices (empty cinema) |

`init-db` does not change tables that already exist. When a model in `model.py` changes,
use `reset-db` (and then `create-admin` again).

## Routes

Use these endpoint names with `url_for` in templates and redirects.

| Endpoint                  | URL                                 | Method | Access     |
|---------------------------|-------------------------------------|--------|------------|
| `main.index`              | `/`                                 | GET    | public     |
| `main.movie_detail`       | `/movie/<movie_id>`                 | GET    | public     |
| `main.movie_poster`       | `/movie/<movie_id>/poster`          | GET    | public     |
| `main.booking`            | `/booking/<showtime_id>`            | GET, POST | logged in |
| `main.my_bookings`        | `/my_bookings`                      | GET    | logged in  |
| `auth.register`           | `/register`                         | GET    | public     |
| `auth.register_post`      | `/register`                         | POST   | public     |
| `auth.login`              | `/login`                            | GET    | public     |
| `auth.login_post`         | `/login`                            | POST   | public     |
| `auth.logout`             | `/logout`                           | GET    | logged in  |
| `admin.manage_movies`     | `/admin/movies`                     | GET    | staff only |
| `admin.new_movie`         | `/admin/movies/new`                 | POST   | staff only |
| `admin.delete_movie`      | `/admin/movies/<movie_id>/delete`   | POST   | staff only |
| `admin.manage_showtimes`  | `/admin/showtimes`                  | GET    | staff only |
| `admin.new_showtime`      | `/admin/showtimes/new`              | POST   | staff only |
| `admin.delete_showtime`   | `/admin/showtimes/<showtime_id>/delete` | POST | staff only |
| `admin.manage_food`       | `/admin/food`                       | GET    | staff only |
| `admin.new_food`          | `/admin/food/new`                   | POST   | staff only |
| `admin.toggle_food`       | `/admin/food/<food_id>/toggle`      | POST   | staff only |
| `admin.delete_food`       | `/admin/food/<food_id>/delete`      | POST   | staff only |

Every `method="post"` form must include the CSRF token, or the server answers 400:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

## Team rules

1. Nobody commits directly to `main`. To enforce it: Settings → Branches → Add branch
   protection rule on `main`, and enable "Require a pull request before merging" (with 1
   approval). This also blocks `git push --force` to `main`.
2. Run `git pull` before you start working every day.
3. One branch per task, and keep them short: 1–2 days is better than 2 weeks.
4. Do not commit `.env`, `.venv/`, `instance/`, passwords or database dumps.
5. Tell the others which files or tables you are going to change, so you don't overwrite each other's work.

## Useful commands

Bring the latest changes from `main` into your branch:
```
git status            # you must be on your branch
git fetch origin
git merge origin/main
```

<img width="406" height="218" alt="Screenshot 2026-10-19 at 16 10 11" src="https://github.com/user-attachments/assets/59b20b1c-6848-49f4-8749-9a97d743c5d2" />