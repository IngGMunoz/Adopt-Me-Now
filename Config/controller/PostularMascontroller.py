from flask import Blueprint, jsonify

from Config.actividad import notificar_postulacion_descartada
from Config.auth import check_admin
from Config.db import db
from Models.postular_mascotas import PostularMascotas
from Models.schemas import PostularMascotasSchema

# API de las mascotas propuestas por usuarios desde /postular (solo administradores).
# El formulario HTML se procesa en la ruta /postular de app.py.
routes_PostularC = Blueprint("routes_PostularC", __name__, url_prefix="/postular")

# Schemas
postular_schema = PostularMascotasSchema()
postulares_schema = PostularMascotasSchema(many=True)


@routes_PostularC.before_request
def require_admin():
    return check_admin()


@routes_PostularC.route("/", methods=["GET"])
def list_postulaciones():
    items = PostularMascotas.query.order_by(PostularMascotas.id.desc()).all()
    return jsonify(postulares_schema.dump(items)), 200

@routes_PostularC.route("/<int:item_id>", methods=["GET"])
def get_postulacion(item_id):
    item = db.get_or_404(PostularMascotas, item_id)
    return jsonify(postular_schema.dump(item)), 200

@routes_PostularC.route("/<int:item_id>", methods=["DELETE"])
def delete_postulacion(item_id):
    item = db.get_or_404(PostularMascotas, item_id)
    notificar_postulacion_descartada(item)
    db.session.delete(item)
    db.session.commit()
    return "", 204
