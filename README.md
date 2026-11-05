# Cinema
Web application for a movie theater with multiple screens. Users can browse movies that are currently showing or will be shown in the next few days, view details of each movie, and book tickets for a specific screening. They can also include popcorn and drinks in their booking. Managing staff add movies and showtimes, and edit the food and beverage items available for sale in the theater.

- Contributors: Alejandra, Haoqi and Martin.

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
├── instance/                # SQLite database, created by Flask (NOT committed)
└── cinema/                  <- Python package with the app
    ├── __init__.py          # create_app(), db
    ├── model.py             # SQLAlchemy models (Movie, Showtime, User, Booking...)
    ├── main.py              # blueprint "main": movies, movie detail, booking, my bookings
    ├── auth.py              # blueprint "auth": register, login, logout + access decorators
    ├── admin.py             # blueprint "admin": manage movies, showtimes, food
    ├── commands.py          # flask init-db / reset-db + demo data
    ├── static/
    │   ├── style.css
    │   ├── bg_page.jpeg
    │   └── posters/         # movie posters (Movie.poster = "posters/<file>")
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

2. Create a `.env` file in the project folder (next to `requirements.txt`):
   ```
   SECRET_KEY=put-something-long-and-random-here
   SQLALCHEMY_DATABASE_URI=sqlite:///cinema.db
   ```
   Each person creates their own `.env`. It is in `.gitignore`, never commit it.

3. Create the tables with demo data:
   ```
   flask --app=cinema init-db
   ```

## Running the app

```
flask --debug --app=cinema run
```

Open http://127.0.0.1:5000 in the browser. Stop the server with Ctrl + C.

Demo accounts created by `init-db`:

| Email            | Password | Role             |
|------------------|----------|------------------|
| admin@cinema.com | admin    | management_staff |
| user@cinema.com  | user     | customer         |

## Database commands

| Command                      | What it does                                                   |
|------------------------------|----------------------------------------------------------------|
| `flask --app=cinema init-db`  | Creates the tables and inserts demo data if the db is empty    |
| `flask --app=cinema reset-db` | DELETES all data and recreates the tables with demo data       |

Use `reset-db` when the models in `model.py` change.

## Routes

Use these endpoint names with `url_for` in templates and redirects.

| Endpoint                 | URL                       | Access     |
|--------------------------|---------------------------|------------|
| `main.index`             | `/`                       | public     |
| `main.movie_detail`      | `/movie/<movie_id>`       | public     |
| `main.booking`           | `/booking/<showtime_id>`  | logged in  |
| `main.my_bookings`       | `/my_bookings`            | logged in  |
| `auth.register`          | `/register`               | public     |
| `auth.login`             | `/login`                  | public     |
| `auth.logout`            | `/logout`                 | public     |
| `admin.manage_movies`    | `/admin/movies`           | staff only |
| `admin.manage_showtimes` | `/admin/showtimes`        | staff only |
| `admin.manage_food`      | `/admin/food`             | staff only |

## Team rules

1. Nobody commits directly to `main`. To enforce it: Settings → Branches → Add branch
   protection rule on `main`, and enable "Require a pull request before merging" (with 1
   approval).
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