# api/__init__.py

from flask import Flask
import os
from dotenv import load_dotenv
from flask_cors import CORS
from .models import db
from .routes import init_app  # Este es el que registra los blueprints
from .commands import setup_commands

load_dotenv()
def create_app():
    # Crea la aplicación Flask
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # Configuración directa desde aquí (ya no desde config.py)
    db_url = os.getenv("DATABASE_URL")
    if db_url is not None:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
            "postgres://", "postgresql://")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv("FLASK_APP_KEY")  # Esto también funcionará para JWT

    # Inicializa la base de datos
    db.init_app(app)

    # Configura CORS
    CORS(app)


    # Configura los comandos personalizados
    setup_commands(app)

    # Registra las rutas
    init_app(app)

    return app
