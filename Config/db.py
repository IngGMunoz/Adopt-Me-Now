import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from dotenv import load_dotenv

# Rutas absolutas del proyecto
BASE_DIR = os.path.dirname(__file__)  # .../Config
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # raíz del repo
TEMPLATE_DIR = os.path.join(BASE_DIR, "Templates")  # plantillas en Config/Templates (main, layouts, components)
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")  # archivos estáticos en /static

# Cargar variables desde .env (si existe) sin pisar las que ya vienen del entorno (Docker)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static",
)

# Clave para firmar las cookies de sesión. En producción SIEMPRE debe venir del entorno.
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

# Base de datos: DATABASE_URL tiene prioridad (útil para despliegue y tests);
# si no existe, se arma la URL de MySQL a partir de las variables DB_*.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "adoptme")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3307")
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
if DATABASE_URL.startswith("mysql"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

# Límite de tamaño de subida (imágenes de mascotas): 5 MB
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# Cookies de sesión más seguras
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

db = SQLAlchemy(app)
ma = Marshmallow(app)
