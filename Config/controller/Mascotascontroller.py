from flask import Blueprint, current_app, request, jsonify, render_template
from Config.auth import check_admin
from Config.db import db
from Models.mascotas import Mascota, MascotaSchema

routes_MascotasC = Blueprint("routes_MascotasC", __name__, url_prefix="/mascotas")

# Schemas
mascota_schema = MascotaSchema()
mascotas_schema = MascotaSchema(many=True)


@routes_MascotasC.before_request
def require_admin_for_writes():
    # Consultar es público; crear, editar y borrar solo lo hace un administrador
    if request.method not in ("GET", "HEAD"):
        return check_admin()


@routes_MascotasC.route("/", methods=["GET"])
def pagina_mascotas():
    mascotas = Mascota.query.filter_by(is_adopted=False).order_by(Mascota.id.desc()).all()
    return render_template("main/Pagina1_Adopcion.html", mascotas=mascotas)


@routes_MascotasC.route("/api", methods=["GET"])
def listar_mascotas():
    items = Mascota.query.order_by(Mascota.id.desc()).all()
    return jsonify({"ok": True, "mascotas": mascotas_schema.dump(items)}), 200


@routes_MascotasC.route("/api", methods=["POST"])
def crear_mascota():
    # Intentar JSON; si no viene (form fallback) leer request.form
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()

    nombre = data.get("nombre")
    descripcion = data.get("descripcion")
    imagen = data.get("imagen") or data.get("imagen_url") or ""
    autor = data.get("autor") or data.get("username") or "Administrador"

    if not nombre or not descripcion:
        return jsonify({"ok": False, "msg": "Faltan campos requeridos: nombre y descripcion"}), 400

    # Evitar duplicados simples
    if Mascota.query.filter(Mascota.nombre == nombre, Mascota.autor == autor).first():
        return jsonify({"ok": False, "msg": "Mascota ya registrada"}), 409

    m = Mascota(nombre=nombre, descripcion=descripcion, imagen=imagen, autor=autor)
    db.session.add(m)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Error al guardar la mascota")
        return jsonify({"ok": False, "msg": "Error al guardar en la base"}), 500

    return jsonify({"ok": True, "msg": "Mascota creada", "mascota": mascota_schema.dump(m)}), 201


@routes_MascotasC.route("/api/<int:mid>", methods=["PUT"])
def actualizar_mascota(mid):
    m = db.get_or_404(Mascota, mid)
    data = request.get_json(silent=True) or request.form.to_dict()
    if "nombre" in data:
        m.nombre = data.get("nombre", m.nombre)
    if "descripcion" in data:
        m.descripcion = data.get("descripcion", m.descripcion)
    if "imagen" in data:
        m.imagen = data.get("imagen", m.imagen)
    if "autor" in data:
        m.autor = data.get("autor", m.autor)

    db.session.commit()
    return jsonify({"ok": True, "msg": "Mascota actualizada", "mascota": mascota_schema.dump(m)}), 200


@routes_MascotasC.route("/api/<int:mid>", methods=["DELETE"])
def eliminar_mascota(mid):
    m = db.get_or_404(Mascota, mid)
    db.session.delete(m)
    db.session.commit()
    return "", 204
