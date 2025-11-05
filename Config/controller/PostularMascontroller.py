from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from Config.db import db
from Models.postular_mascotas import PostularMascotas, PostularMascotasSchema

routes_PostularC = Blueprint("routes_PostularC", __name__, url_prefix="/postular")

# Schemas
postular_schema = PostularMascotasSchema()
postulares_schema = PostularMascotasSchema(many=True)

@routes_PostularC.route("/init-db", methods=["POST"])
def init_db():
    db.create_all()
    return jsonify({"ok": True, "msg": "Tablas creadas/aseguradas"}), 201

@routes_PostularC.route("/", methods=["GET"])
def list_postulaciones():
    items = PostularMascotas.query.order_by(PostularMascotas.id.desc()).all()
    return jsonify(postulares_schema.dump(items)), 200

@routes_PostularC.route("/<int:item_id>", methods=["GET"])
def get_postulacion(item_id):
    item = PostularMascotas.query.get_or_404(item_id)
    return jsonify(postular_schema.dump(item)), 200

@routes_PostularC.route("/", methods=["POST"])
def create_postulacion():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"ok": False, "msg": "Faltan campos requeridos"}), 400

    if PostularMascotas.query.filter(
        (PostularMascotas.username == username) | (PostularMascotas.email == email)
    ).first():
        return jsonify({"ok": False, "msg": "Usuario o email ya existe"}), 409

    obj = PostularMascotas(username=username, email=email)
    obj.password_hash = generate_password_hash(password)
    db.session.add(obj)
    db.session.commit()
    return jsonify(postular_schema.dump(obj)), 201

@routes_PostularC.route("/<int:item_id>", methods=["PUT"])
def update_postulacion(item_id):
    item = PostularMascotas.query.get_or_404(item_id)
    data = request.get_json() or {}
    item.username = data.get("username", item.username)
    item.email = data.get("email", item.email)
    if "password" in data and data["password"]:
        item.password_hash = generate_password_hash(data["password"])
    db.session.commit()
    return jsonify(postular_schema.dump(item)), 200

@routes_PostularC.route("/<int:item_id>", methods=["DELETE"])
def delete_postulacion(item_id):
    item = PostularMascotas.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"ok": True}), 204

# Registrar blueprint en app.py:
# from Config.controller.PostularMascotas import postular_bp
# app.register_blueprint(postular_bp)