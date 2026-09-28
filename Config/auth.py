"""Helpers de autenticación y autorización compartidos por app.py y los blueprints."""

import os
import uuid
from functools import wraps
from urllib.parse import urlparse

from flask import current_app, flash, jsonify, redirect, request, session, url_for
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def is_authenticated():
    return "user_id" in session


def is_admin():
    return bool(session.get("is_admin"))


def _wants_json():
    return (
        request.path.startswith("/api/")
        or request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def _deny(status, msg):
    """Respuesta de acceso denegado: JSON para la API, redirección al login para páginas."""
    if _wants_json():
        return jsonify({"ok": False, "msg": msg}), status
    flash(msg, "error")
    return redirect(url_for("Iniciar_Sesion", next=request.path))


def _cuenta_vigente():
    """Comprueba que la cuenta de la sesión siga existiendo (y activa, si es de administrador).

    Así, eliminar un usuario o desactivar un administrador le quita el acceso de inmediato,
    aunque ya tuviera la sesión abierta.
    """
    from Config.db import db
    from Models.admins import admin
    from Models.usuario import usuario

    if is_admin():
        cuenta = db.session.get(admin, session.get("user_id"))
        return bool(cuenta and cuenta.active)
    return db.session.get(usuario, session.get("user_id")) is not None


def check_login():
    """Devuelve una respuesta de error si no hay sesión, o None si todo está bien."""
    if not is_authenticated():
        return _deny(401, "Debes iniciar sesión para acceder a esta página")
    if not _cuenta_vigente():
        session.clear()
        return _deny(401, "Tu sesión ya no es válida. Inicia sesión de nuevo.")
    return None


def check_admin():
    """Devuelve una respuesta de error si el usuario no es administrador, o None."""
    denied = check_login()
    if denied:
        return denied
    if not is_admin():
        return _deny(403, "Necesitas permisos de administrador")
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return check_login() or f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return check_admin() or f(*args, **kwargs)

    return decorated


def safe_next_url(target, default="/"):
    """Solo acepta rutas relativas del mismo sitio (evita open redirect con //otro-sitio.com)."""
    if not target or not isinstance(target, str):
        return default
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/") or target.startswith("//"):
        return default
    if "\\" in target:
        return default
    return target


def save_uploaded_image(file_storage):
    """Guarda una imagen en static/uploads con nombre único. Devuelve el nombre o "" si no es válida."""
    if not file_storage or not file_storage.filename:
        return ""
    safe_name = secure_filename(file_storage.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return ""
    uploads_dir = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{safe_name}"
    file_storage.save(os.path.join(uploads_dir, filename))
    return filename
