from flask import Flask, Blueprint, render_template

# 1. Creamos la aplicación principal de Flask
app = Flask(__name__)

# 2. Tu Blueprint (si lo usas)
main = Blueprint('main', __name__)

@main.route('/')
def index():
    fake_movies = [
        {"id": 1, "title": "Inception", "genre": "Ciencia Ficción", "duration": 148, "age_rating": "12+", "poster": "inception.jpg"},
        {"id": 2, "title": "Interstellar", "genre": "Aventura / Sci-Fi", "duration": 169, "age_rating": "APTA", "poster": "interstellar.jpg"}
    ]
    return render_template('index.html', movies=fake_movies)

# 3. Registramos el Blueprint en la app
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)
