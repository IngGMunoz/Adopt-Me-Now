from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# Configure absolute paths
BASE_DIR = os.path.dirname(__file__)  # .../Config
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # repo root
TEMPLATE_DIR = os.path.join(BASE_DIR, 'Templates')  # HTML templates live in Config/Templates (includes main, layouts, components)
STATIC_DIR = os.path.join(PROJECT_ROOT, 'static')  # serve static from repo-level /static

app = Flask(
	__name__,
	template_folder=TEMPLATE_DIR,
	static_folder=STATIC_DIR,
	static_url_path='/static'
)

#creamos las credenciales para conectarnos a la bd
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/mysql'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = "web"

#creamos los objetos de bd

db = SQLAlchemy(app)
ma = Marshmallow(app)