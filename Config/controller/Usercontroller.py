from flask import Blueprint, request, jsonify                                
from Config.db import db
from Models.mascotas import Mascota, MascotaSchema   # Importa el modelo y schema tabla mascotas

routes_UserC = Blueprint("routes_UserC", __name__)

# Schemas
mascota_schema = MascotaSchema()
mascotas_schema = MascotaSchema(many=True)

@routes_UserC.route("/init-db", methods=["POST"])
def init_db():
    db.create_all()
    return jsonify({"ok": True, "msg": "Tablas creadas/aseguradas"}), 201

@routes_UserC.route("/mascotas", methods=["GET"])
def listar_mascotas():
    items = Mascota.query.order_by(Mascota.id.desc()).all()
    return jsonify(mascotas_schema.dump(items)), 200

@routes_UserC.route("/mascotas", methods=["POST"])
def crear_mascota():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre")
    descripcion = data.get("descripcion")
    imagen = data.get("imagen")       # nombre de archivo o URL
    autor = data.get("autor", "Administrador")

    if not all([nombre, descripcion, imagen]):
        return jsonify({"ok": False, "msg": "Faltan campos requeridos"}), 400

    m = Mascota(nombre=nombre, descripcion=descripcion, imagen=imagen, autor=autor)
    db.session.add(m)
    db.session.commit()
    return jsonify(mascota_schema.dump(m)), 201