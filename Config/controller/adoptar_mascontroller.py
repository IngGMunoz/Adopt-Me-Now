from datetime import datetime
from flask import Blueprint, request, jsonify, abort
from Config.db import db
from Models.adoptar_mascotas import adoptar_mascotas, adoptar_mascotasSchema

Routes_adoptarC = Blueprint("Routes_adoptarC", __name__, url_prefix="/adopcion")

# Schemas (singular y plural)
adoptar_mascota_schema = adoptar_mascotasSchema()
adoptar_mascotas_schema = adoptar_mascotasSchema(many=True)


@Routes_adoptarC.route("/init-db", methods=["POST"])
def init_db():
    db.create_all()
    return jsonify({"ok": True, "msg": "Tablas creadas/aseguradas"}), 201


@Routes_adoptarC.route("/", methods=["GET"])
def list_adoptions():
    items = adoptar_mascotas.query.order_by(adoptar_mascotas.adoption_date.desc()).all()
    return jsonify({"ok": True, "adoptions": adoptar_mascotas_schema.dump(items)}), 200


@Routes_adoptarC.route("/<int:aid>", methods=["GET"])
def get_adoption(aid):
    item = adoptar_mascotas.query.get_or_404(aid)
    return jsonify({"ok": True, "adoption": adoptar_mascota_schema.dump(item)}), 200


@Routes_adoptarC.route("/", methods=["POST"])
def create_adoption():
    data = request.get_json(silent=True) or {}
    mascota_id = data.get("mascota_id")
    adopter_id = data.get("adopter_id")
    is_confirmed = data.get("is_confirmed", False)

    if not all([mascota_id, adopter_id]):
        return jsonify({"ok": False, "msg": "Faltan campos requeridos: mascota_id y adopter_id"}), 400

    # crear registro de adopción
    a = adoptar_mascotas(mascota_id=mascota_id, adopter_id=adopter_id)
    a.is_confirmed = bool(is_confirmed)
    a.adoption_date = datetime.utcnow() if a.is_confirmed else None

    db.session.add(a)
    db.session.commit()
    return jsonify({"ok": True, "msg": "Adopción registrada", "adoption": adoptar_mascota_schema.dump(a)}), 201


@Routes_adoptarC.route("/<int:aid>", methods=["PUT"])
def update_adoption(aid):
    a = adoptar_mascotas.query.get_or_404(aid)
    data = request.get_json(silent=True) or {}

    if "mascota_id" in data:
        a.mascota_id = data.get("mascota_id")
    if "adopter_id" in data:
        a.adopter_id = data.get("adopter_id")
    if "is_confirmed" in data:
        confirmed = bool(data.get("is_confirmed"))
        if confirmed and not a.is_confirmed:
            a.adoption_date = datetime.utcnow()
        if not confirmed:
            a.adoption_date = None
        a.is_confirmed = confirmed
    if "adoption_date" in data:
        # opcional: permitir setear fecha explícita (ISO string)
        try:
            a.adoption_date = datetime.fromisoformat(data.get("adoption_date"))
        except Exception:
            pass

    db.session.commit()
    return jsonify({"ok": True, "msg": "Adopción actualizada", "adoption": adoptar_mascota_schema.dump(a)}), 200


@Routes_adoptarC.route("/<int:aid>/confirm", methods=["POST"])
def confirm_adoption(aid):
    a = adoptar_mascotas.query.get_or_404(aid)
    if a.is_confirmed:
        return jsonify({"ok": False, "msg": "Ya está confirmada"}), 400
    a.is_confirmed = True
    a.adoption_date = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True, "msg": "Adopción confirmada", "adoption": adoptar_mascota_schema.dump(a)}), 200


@Routes_adoptarC.route("/<int:aid>/unconfirm", methods=["POST"])
def unconfirm_adoption(aid):
    a = adoptar_mascotas.query.get_or_404(aid)
    if not a.is_confirmed:
        return jsonify({"ok": False, "msg": "No está confirmada"}), 400
    a.is_confirmed = False
    a.adoption_date = None
    db.session.commit()
    return jsonify({"ok": True, "msg": "Adopción desconfirmada", "adoption": adoptar_mascota_schema.dump(a)}), 200


@Routes_adoptarC.route("/<int:aid>", methods=["DELETE"])
def delete_adoption(aid):
    a = adoptar_mascotas.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    return jsonify({"ok": True, "msg": "Adopción eliminada"}), 204