from flask import Blueprint, request, jsonify
from Config.db import db
from Models.admins import admin, adminSchema
from Models.usuario import usuario, usuarioSchema
from Models.mascotas import Mascota, MascotaSchema
from Models.postular_mascotas import PostularMascotas, PostularMascotasSchema
from werkzeug.security import generate_password_hash
import os
from flask import current_app, redirect, request, jsonify, url_for
from werkzeug.utils import secure_filename
import uuid

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


@Routes_adminC.route("/init-db", methods=["POST"])
def admin_init_db():
    db.create_all()
    return jsonify({"ok": True, "msg": "Tablas creadas/aseguradas"}), 201


# Admins CRUD
@Routes_adminC.route("/admins", methods=["GET"])
def admin_list_admins():
    items = admin.query.order_by(admin.id.desc()).all()
    return jsonify(admins_schema.dump(items)), 200

@Routes_adminC.route("/admins/<int:aid>", methods=["GET"])
def admin_get_admin(aid):
    a = admin.query.get_or_404(aid)
    return jsonify(admin_schema.dump(a)), 200

@Routes_adminC.route("/admins", methods=["POST"])
def admin_create_admin():
    data = request.get_json() or {}
    username = data.get("username"); email = data.get("email"); password = data.get("password")
    if not all([username, email, password]):
        return jsonify({"ok": False, "msg": "Faltan campos"}), 400
    if admin.query.filter((admin.username == username) | (admin.email == email)).first():
        return jsonify({"ok": False, "msg": "Admin ya existe"}), 409
    a = admin(username=username, email=email, role=data.get("role","admin"))
    a.set_password(password)
    db.session.add(a); db.session.commit()
    return jsonify(admin_schema.dump(a)), 201

@Routes_adminC.route("/admins/<int:aid>", methods=["PUT"])
def admin_update_admin(aid):
    a = admin.query.get_or_404(aid)
    data = request.get_json() or {}
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
    a = admin.query.get_or_404(aid)
    db.session.delete(a); db.session.commit()
    return jsonify({"ok": True}), 204


# Usuarios CRUD (admin)
@Routes_adminC.route("/users", methods=["GET"])
def admin_list_users():
    items = usuario.query.order_by(usuario.id.desc()).all()
    return jsonify(usuarios_schema.dump(items)), 200

@Routes_adminC.route("/users/<int:uid>", methods=["GET"])
def admin_get_user(uid):
    u = usuario.query.get_or_404(uid)
    return jsonify(usuario_schema.dump(u)), 200

@Routes_adminC.route("/users/<int:uid>", methods=["PUT"])
def admin_update_user(uid):
    u = usuario.query.get_or_404(uid)
    data = request.get_json() or {}
    u.username = data.get("username", u.username)
    u.email = data.get("email", u.email)
    if data.get("password"):
        u.set_password(data["password"])
    db.session.commit()
    return jsonify(usuario_schema.dump(u)), 200

@Routes_adminC.route("/users/<int:uid>", methods=["DELETE"])
def admin_delete_user(uid):
    u = usuario.query.get_or_404(uid)
    db.session.delete(u); db.session.commit()
    return jsonify({"ok": True}), 204


# Mascotas CRUD (admin)
@Routes_adminC.route("/mascotas", methods=["GET"])
def admin_list_mascotas():
    items = Mascota.query.order_by(Mascota.id.desc()).all()
    return jsonify(mascotas_schema.dump(items)), 200

@Routes_adminC.route("/mascotas/<int:mid>", methods=["GET"])
def admin_get_mascota(mid):
    m = Mascota.query.get_or_404(mid)
    return jsonify(mascota_schema.dump(m)), 200

@Routes_adminC.route("/mascotas", methods=["POST"])
def admin_create_mascota():
    """
    Acepta JSON (API) o multipart/form-data (form del admin).
    Si viene file en form-data guarda en static/uploads y crea Mascota.
    Devuelve JSON si la petición es JSON; si viene de formulario redirige al referrer.
    """
    # intentar JSON primero (API)
    data = request.get_json(silent=True)
    imagen_filename = ""
    autor = None

    if data:
        # petición JSON
        nombre = data.get("nombre")
        descripcion = data.get("descripcion")
        autor = data.get("autor") or "Administrador"
        imagen_filename = data.get("imagen", "") or ""
    else:
        # fallback: form multipart/form-data (desde postularADM.html)
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        autor = request.form.get("autor") or "Administrador"
        file = request.files.get("imagen")
        if file and file.filename:
            uploads_dir = os.path.join(current_app.static_folder, "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            safe_name = secure_filename(file.filename)
            imagen_filename = f"{uuid.uuid4().hex}_{safe_name}"
            file.save(os.path.join(uploads_dir, imagen_filename))

    if not nombre or not descripcion:
        # responder JSON o redirigir con error simple
        if data:
            return jsonify({"ok": False, "msg": "Faltan campos: nombre y descripcion"}), 400
        return redirect(request.referrer or "/postularADM")

    # evitar duplicados simples
    if Mascota.query.filter(Mascota.nombre == nombre, Mascota.autor == autor).first():
        if data:
            return jsonify({"ok": False, "msg": "Mascota ya registrada"}), 409
        return redirect(request.referrer or "/postularADM")

    # Crear registro en Mascota y también crear una entrada espejo en PostularMascotas
    m = Mascota(nombre=nombre, descripcion=descripcion, imagen=imagen_filename, autor=autor)
    p = PostularMascotas(username=autor, nombre=nombre, descripcion=descripcion, imagen=imagen_filename)
    db.session.add(m)
    db.session.add(p)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if data:
            return jsonify({"ok": False, "msg": "Error al guardar en la BD", "error": str(e)}), 500
        return redirect(request.referrer or "/postularADM")

    if data:
        return jsonify(mascota_schema.dump(m)), 201

    # petición desde formulario: redirigir de vuelta a la página de postularADM
    return redirect(request.referrer or "/postularADM")

@Routes_adminC.route("/mascotas/<int:mid>", methods=["PUT"])
def admin_update_mascota(mid):
    m = Mascota.query.get_or_404(mid)
    data = request.get_json() or {}
    m.nombre = data.get("nombre", m.nombre)
    m.descripcion = data.get("descripcion", m.descripcion)
    m.imagen = data.get("imagen", m.imagen)
    m.autor = data.get("autor", m.autor)
    m.is_adopted = data.get("is_adopted", m.is_adopted)
    db.session.commit()
    return jsonify(mascota_schema.dump(m)), 200

@Routes_adminC.route("/mascotas/<int:mid>", methods=["DELETE"])
def admin_delete_mascota(mid):
    m = Mascota.query.get_or_404(mid)
    db.session.delete(m); db.session.commit()
    return jsonify({"ok": True}), 204


# Postulaciones CRUD (admin)
@Routes_adminC.route("/postulares", methods=["GET"])
def admin_list_postulares():
    items = PostularMascotas.query.order_by(PostularMascotas.id.desc()).all()
    return jsonify(postulares_schema.dump(items)), 200

@Routes_adminC.route("/postulares/<int:pid>", methods=["GET"])
def admin_get_postular(pid):
    p = PostularMascotas.query.get_or_404(pid)
    return jsonify(postular_schema.dump(p)), 200

@Routes_adminC.route("/postulares/<int:pid>", methods=["PUT"])
def admin_update_postular(pid):
    p = PostularMascotas.query.get_or_404(pid)
    data = request.get_json() or {}
    p.username = data.get("username", p.username)
    p.email = data.get("email", p.email)
    if data.get("password"):
        p.set_password(data["password"])
    db.session.commit()
    return jsonify(postular_schema.dump(p)), 200

@Routes_adminC.route("/postulares/<int:pid>", methods=["DELETE"])
def admin_delete_postular(pid):
    p = PostularMascotas.query.get_or_404(pid)
    db.session.delete(p); db.session.commit()
    return jsonify({"ok": True}), 204


# Operaciones de adopción (admin)
@Routes_adminC.route("/mascotas/<int:mid>/adopt", methods=["POST"])
def admin_adopt_mascota(mid):
    m = Mascota.query.get_or_404(mid)
    if m.is_adopted:
        return jsonify({"ok": False, "msg": "Ya adoptada"}), 400
    data = request.get_json() or {}
    m.is_adopted = True
    if data.get("adopter_name"):
        m.autor = data.get("adopter_name")
    db.session.commit()
    return jsonify(mascota_schema.dump(m)), 200

@Routes_adminC.route("/mascotas/<int:mid>/unadopt", methods=["POST"])
def admin_unadopt_mascota(mid):
    m = Mascota.query.get_or_404(mid)
    if not m.is_adopted:
        return jsonify({"ok": False, "msg": "No estaba adoptada"}), 400
    m.is_adopted = False
    db.session.commit()
    return jsonify(mascota_schema.dump(m)), 200

@Routes_adminC.route("/mascotas/form", methods=["POST"])
def admin_create_mascota_form():
    """
   
    """
    # detecta si es request XHR (fetch con header X-Requested-With)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # obtiene datos desde form-data o JSON
    data_json = request.get_json(silent=True)
    if data_json:
        nombre = data_json.get('nombre')
        descripcion = data_json.get('descripcion')
        autor = data_json.get('autor') or 'Administrador'
        imagen_filename = data_json.get('imagen','')
    else:
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        autor = request.form.get('autor') or 'Administrador'
        file = request.files.get('imagen')
        imagen_filename = ""
        if file and file.filename:
            uploads_dir = os.path.join(current_app.static_folder, "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            safe_name = secure_filename(file.filename)
            imagen_filename = f"{uuid.uuid4().hex}_{safe_name}"
            file.save(os.path.join(uploads_dir, imagen_filename))

    if not nombre or not descripcion:
        if is_xhr:
            return jsonify({"ok": False, "msg": "Faltan campos: nombre y descripcion"}), 400
        return redirect('/postularADM')

    # evitar duplicados simples
    if Mascota.query.filter(Mascota.nombre == nombre, Mascota.autor == autor).first():
        if is_xhr:
            return jsonify({"ok": False, "msg": "Mascota ya registrada"}), 409
        return redirect('/postularADM')

    # Also create a PostularMascotas row so admin posts appear there as well
    m = Mascota(nombre=nombre, descripcion=descripcion, imagen=imagen_filename, autor=autor)
    p = PostularMascotas(username=autor, nombre=nombre, descripcion=descripcion, imagen=imagen_filename)
    db.session.add(m)
    db.session.add(p)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if is_xhr:
            return jsonify({"ok": False, "msg": "Error al guardar en la BD", "error": str(e)}), 500
        return redirect('/postularADM')

    # Si XHR: devolver JSON con el registro creado para que el frontend lo muestre inmediatamente.
    if is_xhr:
        return jsonify({"ok": True, "mascota": mascota_schema.dump(m)}), 201

    # fallback: petición de formulario tradicional -> redirigir a la página que lista las mascotas
    return redirect('/postularADM')

