# Cinema
Web application for a movie theater with multiple screens. Users can browse movies that are currently showing or will be shown in the next few days, view details of each movie, and book tickets for a specific screening. They can also include popcorn and drinks in their booking. Managing staff add movies and showtimes, and edit the food and beverage items available for sale in the theater.

- Contributors: Alejandra, Haoqi and Martin.

## Cómo arrancar la app

1. Instalar dependencias (una sola vez por ordenador):
   ```
   py -m pip install -r requirements.txt
   ```

2. Arrancar el servidor:
   ```
   py mainpage.py
   ```
   Abre http://127.0.0.1:5000 en el navegador. La primera vez se crea
   el archivo `instance/cinema.db` con todas las tablas vacías.

3. Para parar el servidor: Ctrl + C en el terminal.

## Crear admin y precios de prueba (una vez por ordenador)

La BD arranca vacía. Para poder entrar como admin y para que las reservas
tengan precio, abre el terminal de Python:

```
py
```

Y pega esto dentro:

```python
from mainpage import app, db
from model import User, UserRole, TicketPrice
from werkzeug.security import generate_password_hash
from decimal import Decimal

with app.app_context():
    db.session.add(User(
        email="admin@cinema.com",
        password_hash=generate_password_hash("admin"),
        role=UserRole.management_staff,
    ))
    for dow in range(7):
        db.session.add(TicketPrice(
            day_of_week=dow,
            price=Decimal("7.00") if dow < 5 else Decimal("9.00"),
        ))
    db.session.commit()

exit()
```

Usuario de prueba: `admin@cinema.com` / `admin`. Los clientes se registran
desde la web en `/register`.

## Resetear la BD

Si cambian las tablas y hay que empezar de cero:

```
Remove-Item instance\cinema.db
py mainpage.py        # vuelve a crear las tablas vacías
```

## Reglas de equipo

1. Nadie hace commit directo a main. Para forzarlo: Settings → Branches → Add branch
protection rule sobre main, y activad Require a pull request before merging (con 1
aprobación).
2. Hacer git pull antes de empezar a trabajar cada día.
3. Una rama por tarea, y cortas: mejor de 1 a 2 días que 2 semanas.
4. No subir .env, node modules/, contraseñas ni volcados de la base de datos.
5. Avisar de qué archivos o tablas vais a tocar para no pisaros.

# COMANDOS UTILES 
Para tener las actualizaciones del main en una rama:
git status (tienes que estar en tu rama)
git fetch origin
git merge origin/main

<img width="406" height="218" alt="Screenshot 2026-10-19 at 16 10 11" src="https://github.com/user-attachments/assets/59b20b1c-6848-49f4-8749-9a97d743c5d2" />




