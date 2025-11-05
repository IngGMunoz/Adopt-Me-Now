from flask import Blueprint, request, jsonify, abort
from Config.db import db
from Models.adoptar_mascotas import adoptar_mascotas, adoptar_mascotasSchema

Routes_adoptarC = Blueprint("Routes_adoptarC", __name__, url_prefix="/adopcion")

# Schemas
adoptar_mascota_schema = adoptar_mascotasSchema()
adoptar_mascota_schema = adoptar_mascotasSchema(many=True)


@Routes_adoptarC.route("/init-db", methods=["POST"])
def init_db():
    db.create_all()
    return jsonify({"ok": True, "msg": "Tablas creadas/aseguradas"}), 201


@Routes_adoptarC.route("/", methods=["GET"])
def list_available():
    items = adoptar_mascotas.query.filter_by(is_adopted=False).order_by(adoptar_mascotas.id.desc()).all()
    return jsonify(adoptar_mascota_schema.dump(items)), 200


@Routes_adoptarC.route("/adopted", methods=["GET"])
def list_adopted():
    items = adoptar_mascotas.query.filter_by(is_adopted=True).order_by(adoptar_mascotas.id.desc()).all()
    return jsonify(adoptar_mascota_schema.dump(items)), 200


@Routes_adoptarC.route("/<int:mascota_id>", methods=["GET"])
def get_mascota(mascota_id):
    m = adoptar_mascotas.query.get_or_404(mascota_id)
    return jsonify(adoptar_mascota_schema.dump(m)), 200


@Routes_adoptarC.route("/<int:mascota_id>/adopt", methods=["POST"])
def adopt_mascota(mascota_id):
    m = adoptar_mascotas.query.get_or_404(mascota_id)
    if m.is_adopted:
        return jsonify({"ok": False, "msg": "Mascota ya adoptada"}), 400

    data = request.get_json(silent=True) or {}
    adopter_name = data.get("adopter_name")
    # opcional: email u otros datos
    # si quieres guardar datos del adoptante crea un modelo Adopcion; aquí solo marcamos adoptada
    m.is_adopted = True
    if adopter_name:
        # Nota: esto sobrescribe autor; si no quieres eso crea campo 'adopted_by' en el modelo
        m.autor = adopter_name
    db.session.commit()
    return jsonify(adoptar_mascota_schema.dump(m)), 200


@Routes_adoptarC.route("/<int:mascota_id>/unadopt", methods=["POST"])
def unadopt_mascota(mascota_id):
    m = adoptar_mascotas.query.get_or_404(mascota_id)
    if not m.is_adopted:
        return jsonify({"ok": False, "msg": "Mascota no está adoptada"}), 400
    m.is_adopted = False
    db.session.commit()
    return jsonify(adoptar_mascota_schema.dump(m)), 200