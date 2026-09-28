import os
import sys
import tempfile

import pytest

# Configurar el entorno ANTES de importar la app: SQLite temporal en lugar de MySQL
_tmpdir = tempfile.mkdtemp(prefix="adoptme-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_tmpdir, "test.db")
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ADMIN_REGISTRATION_CODE"] = "codigo-test"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app  # noqa: E402
from Config.db import db  # noqa: E402
from Models.admins import admin  # noqa: E402
from Models.usuario import usuario  # noqa: E402


@pytest.fixture
def app(tmp_path):
    flask_app.config.update(TESTING=True)
    # Las imágenes subidas en los tests van a una carpeta temporal, no a static/uploads
    original_static = flask_app.static_folder
    flask_app.static_folder = str(tmp_path)
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
    flask_app.static_folder = original_static


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    u = usuario(username="ana", email="ana@example.com")
    u.set_password("secreta123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def admin_user(app):
    a = admin(username="root", email="root@example.com")
    a.set_password("adminpass123")
    db.session.add(a)
    db.session.commit()
    return a


def login(client, identifier, password):
    return client.post("/api/users/login", json={"identifier": identifier, "password": password})
