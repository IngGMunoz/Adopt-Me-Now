import hmac
import os

from flask import Blueprint, current_app, jsonify, request, session

from Config.actividad import enviar_correo, notificar_postulacion_descartada, registrar
from Config.auth import check_admin, is_admin, save_uploaded_image
from Config.db import db
from Models.admins import admin
from Models.usuario import usuario
from Models.mascotas import Mascota
from Models.postular_mascotas import PostularMascotas
from Models.schemas import MascotaSchema, PostularMascotasSchema, adminSchema, usuarioSchema
from Models.adoptar_mascotas import adoptar_mascotas

Routes_adminC = Blueprint("routes_adminC", __name__, url_prefix="/api/admin")

# Schemas
admin_schema = adminSchema()
admins_schema = adminSchema(many=True)

usuario_schema = usuarioSchema()
usuarios_schema = usuarioSchema(many=True)

mascota_schema = MascotaSchema()
mascotas_schema = MascotaSchema(many=True)

postular_schema = PostularMascotasSchema()
postulares_schema = PostularMascotasSchema(many=True)


def _valid_registration_code(code):
    expected = os.getenv("ADMIN_REGISTRATION_CODE")
    return bool(expected and code) and hmac.compare_digest(str(code), expected)


@Routes_adminC.before_request
def require_admin():
    # Único endpoint abierto: registrar un admin nuevo con el código de registro
    if request.endpoint == "routes_adminC.admin_create_admin":
        return None
    return check_admin()


# Admins CRUD
@Routes_adminC.route("/admins", methods=["GET"])
def admin_list_admins():
    items = admin.query.order_by(admin.id.desc()).all()
    return jsonify(admins_schema.dump(items)), 200

@Routes_adminC.route("/admins/<int:aid>", methods=["GET"])
def admin_get_admin(aid):
    a = db.get_or_404(admin, aid)
    return jsonify(admin_schema.dump(a)), 200

@Routes_adminC.route("/admins", methods=["POST"])
def admin_create_admin():
    data = request.get_json(silent=True) or {}
    if not is_admin() and not _valid_registration_code(data.get("codigo")):
        return jsonify({"ok": False, "msg": "Código de registro de administrador inválido"}), 403

    username = data.get("username"); email = data.get("email"); password = data.get("password")
    if not all([username, email, password]):
        return jsonify({"ok": False, "msg": "Faltan campos"}), 400
    if len(password) < 8:
        return jsonify({"ok": False, "msg": "La contraseña debe tener al menos 8 caracteres"}), 400
    if admin.query.filter((admin.username == username) | (admin.email == email)).first():
        return jsonify({"ok": False, "msg": "Admin ya existe"}), 409
    # Solo un admin con sesión puede asignar roles distintos a "admin"
    role = data.get("role", "admin") if is_admin() else "admin"
    a = admin(username=username, email=email, role=role)
    a.set_password(password)
    db.session.add(a); db.session.commit()
    return jsonify(admin_schema.dump(a)), 201

def _as_bool(value):
    """Interpreta true/false aunque llegue como texto ("false" no debe contar como verdadero)."""
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "si", "sí", "yes", "on")
    return bool(value)


@Routes_adminC.route("/admins/<int:aid>", methods=["PUT"])
def admin_update_admin(aid):
    a = db.get_or_404(admin, aid)
    data = request.get_json(silent=True) or {}
    if "active" in data:
        active = _as_bool(data["active"])
        if not active and aid == session.get("user_id"):
            return jsonify({"ok": False, "msg": "No puedes desactivar tu propia cuenta"}), 400
        a.active = active
    a.username = data.get("username", a.username)
    a.email = data.get("email", a.email)
    a.role = data.get("role", a.role)
    if data.get("password"):
        a.set_password(data["password"])
    db.session.commit()
    return jsonify(admin_schema.dump(a)), 200

@Routes_adminC.route("/admins/<int:aid>", methods=["DELETE"])
def admin_delete_admin(aid):
    # Quien elimina es otro admin activo, así que el sistema nunca se queda sin administradores
    if aid == session.get("user_id"):
        return jsonify({"ok": False, "msg": "No puedes eliminar tu propia cuenta"}), 400
    a = db.get_or_404(admin, aid)
    db.session.delete(a); db.session.commit()
    return "", 204


# Usuarios CRUD (admin)
@Routes_adminC.route("/users", methods=["GET"])
def admin_list_users():
    items = usuario.query.order_by(usuario.id.desc()).all()
    return jsonify(usuarios_schema.dump(items)), 200

@Routes_adminC.route("/users/<int:uid>", methods=["GET"])
def admin_get_user(uid):
    u = db.get_or_404(usuario, uid)
    return jsonify(usuario_schema.dump(u)), 200

@Routes_adminC.route("/users/<int:uid>", methods=["PUT"])
def admin_update_user(uid):
    u = db.get_or_404(usuario, uid)
    data = request.get_json(silent=True) or {}
    u.username = data.get("username", u.username)
    u.email = data.get("email", u.email)
    if data.get("password"):
        u.set_password(data["password"])
    db.session.commit()
    return jsonify(usuario_schema.dump(u)), 200

@Routes_adminC.route("/users/<int:uid>", methods=["DELETE"])
def admin_delete_user(uid):
    u = db.get_or_404(usuario, uid)
    db.session.delete(u); db.session.commit()
    return "", 204


# Mascotas CRUD (admin)
@Routes_adminC.route("/mascotas", methods=["GET"])
def admin_list_mascotas():
    items = Mascota.query.order_by(Mascota.id.desc()).all()
    return jsonify(mascotas_schema.dump(items)), 200

@Routes_adminC.route("/mascotas/<int:mid>", methods=["GET"])
def admin_get_mascota(mid):
    m = db.get_or_404(Mascota, mid)
    return jsonify(mascota_schema.dump(m)), 200


@Routes_adminC.route("/mascotas", methods=["POST"])
def admin_create_mascota():
    """Publica una mascota desde JSON o multipart/form-data."""
    data = request.get_json(silent=True)
    if data:
        imagen = data.get("imagen") or ""
    else:
        data = request.form
        imagen = save_uploaded_image(request.files.get("imagen"))
    nombre = data.get("nombre")
    descripcion = data.get("descripcion")
    autor = session.get("user_name") or "Administrador"

    if not nombre or not descripcion:
        return jsonify({"ok": False, "msg": "Faltan campos: nombre y descripcion"}), 400
    if Mascota.query.filter_by(nombre=nombre, autor=autor).first():
        return jsonify({"ok": False, "msg": "Mascota ya registrada"}), 409

    m = Mascota(nombre=nombre, descripcion=descripcion, imagen=imagen, autor=autor,
                publicado_por_id=session.get("user_id"), destacada=_as_bool(data.get("destacada")),
                **{c: data.get(c) or None for c in Mascota.CAMPOS})
    db.session.add(m)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Error al guardar la mascota")
        return jsonify({"ok": False, "msg": "Error al guardar en la BD"}), 500
    return jsonify({"ok": True, "mascota": mascota_schema.dump(m)}), 201


@Routes_adminC.route("/mascotas/<int:mid>", methods=["PUT"])
def admin_update_mascota(mid):
    m = db.get_or_404(Mascota, mid)
    data = request.get_json(silent=True) or {}
    for campo in ("nombre", "descripcion", "imagen", "autor") + Mascota.CAMPOS:
        if campo in data:
            setattr(m, campo, data[campo])
    for campo in ("is_adopted", "destacada"):
        if campo in data:
            setattr(m, campo, _as_bool(data[campo]))
    db.session.commit()
    return jsonify(mascota_schema.dump(m)), 200

@Routes_adminC.route("/mascotas/<int:mid>", methods=["DELETE"])
def admin_delete_mascota(mid):
    m = db.get_or_404(Mascota, mid)
    db.session.delete(m); db.session.commit()
    return "", 204


# Postulaciones CRUD (admin)
@Routes_adminC.route("/postulares", methods=["GET"])
def admin_list_postulares():
    items = PostularMascotas.query.order_by(PostularMascotas.id.desc()).all()
    return jsonify(postulares_schema.dump(items)), 200

@Routes_adminC.route("/postulares/<int:pid>", methods=["GET"])
def admin_get_postular(pid):
    p = db.get_or_404(PostularMascotas, pid)
    return jsonify(postular_schema.dump(p)), 200

@Routes_adminC.route("/postulares/<int:pid>", methods=["PUT"])
def admin_update_postular(pid):
    p = db.get_or_404(PostularMascotas, pid)
    data = request.get_json(silent=True) or {}
    for field in ("nombre", "descripcion", "especie", "raza", "edad", "sexo", "tamanio", "color", "ubicacion"):
        if field in data:
            setattr(p, field, data[field])
    db.session.commit()
    return jsonify(postular_schema.dump(p)), 200

@Routes_adminC.route("/postulares/<int:pid>", methods=["DELETE"])
def admin_delete_postular(pid):
    p = db.get_or_404(PostularMascotas, pid)
    notificar_postulacion_descartada(p)
    db.session.delete(p); db.session.commit()
    return "", 204

@Routes_adminC.route("/postulares/<int:pid>/aprobar", methods=["POST"])
def admin_aprobar_postular(pid):
    """Publica la mascota propuesta por un usuario y enlaza la postulación con ella."""
    p = db.get_or_404(PostularMascotas, pid)
    if p.aprobada:
        return jsonify({"ok": False, "msg": "La postulación ya fue aprobada"}), 409
    m = Mascota(
        nombre=p.nombre or "Sin nombre",
        descripcion=p.descripcion_publica(),
        imagen=p.imagen or "",
        autor=session.get("user_name") or "Administrador",
        publicado_por_id=session.get("user_id"),
        **{c: getattr(p, c) for c in Mascota.CAMPOS},
    )
    p.mascota = m
    db.session.add(m)
    db.session.flush()  # m.id para el enlace a su ficha
    texto = f"¡{m.nombre} ya está publicada en el catálogo gracias a tu postulación!"
    registrar(p.usuario_id, "postulacion_publicada", texto, enlace=f"/mascota/{m.id}", commit=False)
    db.session.commit()
    if p.usuario:
        enviar_correo(p.usuario.email, "Tu postulación fue publicada", texto)
    return jsonify({"ok": True, "mascota": mascota_schema.dump(m), "postulacion": postular_schema.dump(p)}), 201


# Solicitudes de adopción (admin)
@Routes_adminC.route("/solicitudes", methods=["GET"])
def admin_list_solicitudes():
    query = adoptar_mascotas.query.order_by(adoptar_mascotas.id.desc())
    if request.args.get("mascota_id", type=int):
        query = query.filter_by(mascota_id=request.args.get("mascota_id", type=int))
    return jsonify([s.to_dict() for s in query.all()]), 200

@Routes_adminC.route("/solicitudes/<int:sid>/confirmar", methods=["POST"])
def admin_confirmar_solicitud(sid):
    """Aprueba una solicitud: la mascota queda adoptada y sale del catálogo."""
    s = db.get_or_404(adoptar_mascotas, sid)
    if s.is_confirmed:
        return jsonify({"ok": False, "msg": "La solicitud ya estaba confirmada"}), 409
    if s.mascota and s.mascota.is_adopted:
        return jsonify({"ok": False, "msg": "La mascota ya fue adoptada"}), 409
    s.is_confirmed = True
    if s.mascota:
        s.mascota.is_adopted = True
    nombre = s.mascota.nombre if s.mascota else (s.pet_name or "la mascota")
    texto = f"¡La fundación aprobó tu solicitud para adoptar a {nombre}! Pronto te contactarán."
    registrar(s.adopter_id, "solicitud_aprobada", texto, commit=False)
    db.session.commit()
    enviar_correo(s.email, "Tu solicitud de adopción fue aprobada", texto)
    return jsonify({"ok": True, "solicitud": s.to_dict()}), 200


# Operaciones de adopción (admin)
@Routes_adminC.route("/mascotas/<int:mid>/adopt", methods=["POST"])
def admin_adopt_mascota(mid):
    m = db.get_or_404(Mascota, mid)
    if m.is_adopted:
        return jsonify({"ok": False, "msg": "Ya adoptada"}), 400
    m.is_adopted = True
    db.session.commit()
    return jsonify(mascota_schema.dump(m)), 200

@Routes_adminC.route("/mascotas/<int:mid>/unadopt", methods=["POST"])
def admin_unadopt_mascota(mid):
    m = db.get_or_404(Mascota, mid)
    if not m.is_adopted:
        return jsonify({"ok": False, "msg": "No estaba adoptada"}), 400
    m.is_adopted = False
    db.session.commit()
    return jsonify(mascota_schema.dump(m)), 200
