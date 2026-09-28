from flask import Blueprint, jsonify, request, session

from Config.actividad import registrar
from Config.auth import (check_admin, check_login, is_admin, limpiar_fallos_login, login_bloqueado,
                         registrar_fallo_login)
from Config.db import db
from Models.usuario import usuario
from Models.schemas import usuarioSchema
from Models.admins import admin as AdminModel

routes_UserC = Blueprint("routes_UserC", __name__, url_prefix="/api/users")

usuario_schema = usuarioSchema()
usuarios_schema = usuarioSchema(many=True)


def _check_self_or_admin(user_id):
    """Un usuario solo puede ver/editar/borrar su propia cuenta; un admin, cualquiera."""
    denied = check_login()
    if denied:
        return denied
    if not is_admin() and session.get("user_id") != user_id:
        return jsonify({"ok": False, "msg": "No autorizado"}), 403
    return None


@routes_UserC.route("/", methods=["GET"])
def list_users():
    denied = check_admin()
    if denied:
        return denied
    users = usuario.query.order_by(usuario.id.desc()).all()
    return jsonify(usuarios_schema.dump(users)), 200


@routes_UserC.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    denied = _check_self_or_admin(user_id)
    if denied:
        return denied
    u = db.get_or_404(usuario, user_id)
    return jsonify(usuario_schema.dump(u)), 200


@routes_UserC.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"ok": False, "msg": "Faltan campos"}), 400

    if usuario.query.filter((usuario.username == username) | (usuario.email == email)).first():
        return jsonify({"ok": False, "msg": "Usuario o email ya existe"}), 409

    u = usuario(username=username, email=email)
    u.set_password(password)
    db.session.add(u)
    db.session.flush()
    registrar(u.id, "registro", "Creaste tu cuenta en Adopt Me", commit=False)
    db.session.commit()
    return jsonify(usuario_schema.dump(u)), 201


@routes_UserC.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = data.get("identifier") or data.get("username") or data.get("email")
    password = data.get("password")
    if not all([identifier, password]):
        return jsonify({"ok": False, "msg": "Faltan credenciales"}), 400
    if login_bloqueado(identifier):
        return jsonify({"ok": False, "msg": "Demasiados intentos fallidos. Espera 15 minutos."}), 429

    # Primero administradores (mismo login para ambos) y luego usuarios
    u = (AdminModel.query.filter((AdminModel.username == identifier) | (AdminModel.email == identifier)).first()
         or usuario.query.filter((usuario.username == identifier) | (usuario.email == identifier)).first())
    if not u or not u.check_password(password):
        registrar_fallo_login(identifier)
        return jsonify({"ok": False, "msg": "Credenciales inválidas"}), 401
    limpiar_fallos_login(identifier)

    session.clear()
    session["user_id"] = u.id
    session["user_name"] = u.username
    session["user_email"] = u.email

    if isinstance(u, AdminModel):
        if not u.active:
            session.clear()
            return jsonify({"ok": False, "msg": "Cuenta de administrador desactivada"}), 403
        session["is_admin"] = True
        admin_data = {"id": u.id, "username": u.username, "email": u.email, "role": u.role}
        return jsonify({"ok": True, "user": admin_data, "redirect": "/postularADM"}), 200

    registrar(u.id, "inicio_sesion", "Iniciaste sesión")
    return jsonify({"ok": True, "user": usuario_schema.dump(u), "redirect": "/"}), 200


@routes_UserC.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True}), 200


@routes_UserC.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    denied = _check_self_or_admin(user_id)
    if denied:
        return denied
    u = db.get_or_404(usuario, user_id)
    data = request.get_json(silent=True) or {}
    u.username = data.get("username", u.username)
    u.email = data.get("email", u.email)
    if data.get("password"):
        u.set_password(data["password"])
    db.session.commit()
    return jsonify(usuario_schema.dump(u)), 200


@routes_UserC.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    denied = _check_self_or_admin(user_id)
    if denied:
        return denied
    u = db.get_or_404(usuario, user_id)
    db.session.delete(u)
    db.session.commit()
    if session.get("user_id") == user_id and not is_admin():
        session.clear()
    return "", 204
