from flask import Blueprint, request, jsonify, session
from Config.db import db
from Models.usuario import usuario, usuarioSchema
from Models.admins import admin as AdminModel
from werkzeug.security import generate_password_hash, check_password_hash

routes_UserC = Blueprint("routes_UserC", __name__, url_prefix="/api/users")

usuario_schema = usuarioSchema()
usuarios_schema = usuarioSchema(many=True)


def find_user(identifier):
    # intentar buscar en admins primero (permitir login de admin desde la misma pantalla)
    a = AdminModel.query.filter((AdminModel.username == identifier) | (AdminModel.email == identifier)).first()
    if a:
        return a
    return usuario.query.filter(
        (usuario.username == identifier) | (usuario.email == identifier)
    ).first()


@routes_UserC.route("/init-db", methods=["POST"])
def init_db():
    db.create_all()
    return jsonify({"ok": True, "msg": "Tablas creadas/aseguradas"}), 201


@routes_UserC.route("/", methods=["GET"])
def list_users():
    users = usuario.query.order_by(usuario.id.desc()).all()
    return jsonify(usuarios_schema.dump(users)), 200


@routes_UserC.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    u = usuario.query.get_or_404(user_id)
    return jsonify(usuario_schema.dump(u)), 200


@routes_UserC.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"ok": False, "msg": "Faltan campos"}), 400

    if usuario.query.filter((usuario.username == username) | (usuario.email == email)).first():
        return jsonify({"ok": False, "msg": "Usuario o email ya existe"}), 409

    u = usuario(username=username, email=email)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return jsonify(usuario_schema.dump(u)), 201


@routes_UserC.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("identifier") or data.get("username") or data.get("email")
    password = data.get("password")
    if not all([identifier, password]):
        return jsonify({"ok": False, "msg": "Faltan credenciales"}), 400

    u = find_user(identifier)
    if not u or not u.check_password(password):
        return jsonify({"ok": False, "msg": "Credenciales inválidas"}), 401

    session.clear()
    session["user_id"] = u.id
    # si es instancia de admin, marcar la sesión
    if isinstance(u, AdminModel):
        session["is_admin"] = True
        session["username"] = u.username
        session["user_email"] = u.email
        # serializar admin manualmente para evitar usar usuario schema
        admin_data = {"id": u.id, "username": u.username, "email": u.email, "role": getattr(u, "role", "admin")}
        return jsonify({"ok": True, "user": admin_data}), 200

    session["username"] = u.username
    session["user_email"] = u.email
    return jsonify({"ok": True, "user": usuario_schema.dump(u)}), 200


@routes_UserC.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True}), 200


@routes_UserC.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    u = usuario.query.get_or_404(user_id)
    data = request.get_json() or {}
    u.username = data.get("username", u.username)
    u.email = data.get("email", u.email)
    if data.get("password"):
        u.set_password(data["password"])
    db.session.commit()
    return jsonify(usuario_schema.dump(u)), 200


@routes_UserC.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    u = usuario.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({"ok": True}), 204