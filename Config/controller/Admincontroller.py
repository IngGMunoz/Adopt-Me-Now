import hmac
import os

from flask import Blueprint, current_app, jsonify, redirect, request, session

from Config.auth import check_admin, is_admin, save_uploaded_image
from Config.db import db
from Models.admins import admin, adminSchema
from Models.usuario import usuario, usuarioSchema
from Models.mascotas import Mascota, MascotaSchema
from Models.postular_mascotas import PostularMascotas, PostularMascotasSchema

# Blueprint del admin (url_prefix organizado)
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

@Routes_adminC.route("/admins/<int:aid>", methods=["PUT"])
def admin_update_admin(aid):
    a = db.get_or_404(admin, aid)
    data = request.get_json(silent=True) or {}
    a.username = data.get("username", a.username)
    a.email = data.get("email", a.email)
    a.role = data.get("role", a.role)
    a.active = data.get("active", a.active)
    if data.get("password"):
        a.set_password(data["password"])
    db.session.commit()
    return jsonify(admin_schema.dump(a)), 200

@Routes_adminC.route("/admins/<int:aid>", methods=["DELETE"])
def admin_delete_admin(aid):
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


def _create_mascota():
    """Crea una Mascota (y su entrada espejo en PostularMascotas) desde JSON o multipart/form-data.

    Devuelve (mascota, error): error es (mensaje, status) si algo falló.
    """
    data = request.get_json(silent=True)
    if data:
        nombre = data.get("nombre")
        descripcion = data.get("descripcion")
        imagen_filename = data.get("imagen", "") or ""
    else:
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        imagen_filename = save_uploaded_image(request.files.get("imagen"))
    autor = session.get("user_name") or "Administrador"

    if not nombre or not descripcion:
        return None, ("Faltan campos: nombre y descripcion", 400)

    # evitar duplicados simples
    if Mascota.query.filter(Mascota.nombre == nombre, Mascota.autor == autor).first():
        return None, ("Mascota ya registrada", 409)

    m = Mascota(nombre=nombre, descripcion=descripcion, imagen=imagen_filename, autor=autor)
    p = PostularMascotas(username=autor, nombre=nombre, descripcion=descripcion, imagen=imagen_filename)
    db.session.add(m)
    db.session.add(p)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Error al guardar la mascota")
        return None, ("Error al guardar en la BD", 500)
    return m, None


@Routes_adminC.route("/mascotas", methods=["POST"])
def admin_create_mascota():
    """API: acepta JSON o multipart/form-data y responde siempre JSON."""
    m, error = _create_mascota()
    if error:
        msg, status = error
        return jsonify({"ok": False, "msg": msg}), status
    return jsonify({"ok": True, "mascota": mascota_schema.dump(m)}), 201


@Routes_adminC.route("/mascotas/form", methods=["POST"])
def admin_create_mascota_form():
    """Envío tradicional del formulario de postularADM.html (fallback sin JavaScript)."""
    _create_mascota()
    return redirect("/postularADM")


@Routes_adminC.route("/mascotas/<int:mid>", methods=["PUT"])
def admin_update_mascota(mid):
    m = db.get_or_404(Mascota, mid)
    data = request.get_json(silent=True) or {}
    m.nombre = data.get("nombre", m.nombre)
    m.descripcion = data.get("descripcion", m.descripcion)
    m.imagen = data.get("imagen", m.imagen)
    m.autor = data.get("autor", m.autor)
    m.is_adopted = data.get("is_adopted", m.is_adopted)
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
    db.session.delete(p); db.session.commit()
    return "", 204


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
