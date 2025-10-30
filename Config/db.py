import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# Configure absolute paths
BASE_DIR = os.path.dirname(__file__)  # .../Config
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # repo root
TEMPLATE_DIR = os.path.join(
    BASE_DIR, "Templates"
)  # HTML templates live in Config/Templates (includes main, layouts, components)
STATIC_DIR = os.path.join(
    PROJECT_ROOT, "static"
)  # serve static from repo-level /static

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static",
    
)

# Usa env vars (Docker) y fallback local (host)
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "12345")
DB_NAME = os.getenv("DB_NAME", "mysql1")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3307")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

db = SQLAlchemy(app)
ma = Marshmallow(app)
# ...existing code...