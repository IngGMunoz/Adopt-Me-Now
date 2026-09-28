import os
from datetime import date

from flask import flash, jsonify, redirect, render_template, request, session, url_for

from Config.db import app, db
from Config.auth import (
    admin_required,
    csrf_protect,
    csrf_token,
    is_authenticated,
    limpiar_fallos_login,
    login_bloqueado,
    login_required,
    registrar_fallo_login,
    safe_next_url,
    save_uploaded_image,
)
from Config.schema import init_db
from Config.demo import proteger_cuentas_demo
from Config.actividad import agrupar_por_dia, registrar
import Config.filtros  # noqa: F401  (filtros de fecha para las plantillas)

# Modelos
from Models.mascotas import Mascota
from Models.postular_mascotas import PostularMascotas
from Models.admins import admin as AdminModel
from Models.adoptar_mascotas import adoptar_mascotas
from Models.usuario import usuario
from Models.actividad import Actividad
from sqlalchemy import func

# Blueprints (API)
from Config.controller.Usercontroller import routes_UserC
from Config.controller.Admincontroller import Routes_adminC
from Config.controller.Cuentacontroller import routes_CuentaC

app.register_blueprint(routes_UserC)
app.register_blueprint(Routes_adminC)
app.register_blueprint(routes_CuentaC)

app.before_request(csrf_protect)
app.before_request(proteger_cuentas_demo)

# Crear tablas y ajustar el esquema al iniciar la app
with app.app_context():
    init_db()


def _wants_json():
    # Los navegadores envían "Accept: */*", así que accept_json siempre sería True:
    # solo se responde JSON a peticiones fetch/XHR o que prefieran JSON sobre HTML.
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    best = request.accept_mimetypes.best_match(["text/html", "application/json"])
    return best == "application/json"


def get_current_user():
    if "user_id" not in session:
        return None
    if session.get("is_admin"):
        return {
            "id": session.get("user_id"),
            "email": session.get("user_email"),
            "nombre": session.get("user_name"),
            "is_admin": True,
        }
    u = db.session.get(usuario, session["user_id"])
    if not u:
        return None
    return {"id": u.id, "email": u.email, "nombre": u.username}


# Información de autenticación disponible en todas las plantillas
@app.context_processor
def inject_auth():
    return {
        "is_authenticated": is_authenticated(),
        "current_user": get_current_user(),
        "now_year": date.today().year,
        "csrf_token": csrf_token,
    }


@app.errorhandler(413)
def file_too_large(_error):
    flash("La imagen es demasiado grande (máximo 5 MB)", "error")
    return redirect(request.referrer or "/")


# ---------------------------------------------------------------------------
# Páginas públicas
# ---------------------------------------------------------------------------

@app.route("/")
def Pagina_Principal():
    # Tres mascotas para el inicio: primero las destacadas y luego las más recientes
    try:
        disponibles = Mascota.query.filter_by(is_adopted=False)
        inicio = disponibles.order_by(Mascota.destacada.desc(), Mascota.id.desc()).limit(3).all()
        total = disponibles.count()
        adoptadas = Mascota.query.filter_by(is_adopted=True).count()
    except Exception:
        app.logger.exception("No se pudieron cargar las mascotas")
        inicio, total, adoptadas = [], 0, 0
    return render_template(
        "main/Pagina_Principal.html",
        mascotas=inicio,
        total_disponibles=total,
        total_adoptadas=adoptadas,
    )


@app.route("/adopcion")
def Pagina_Adopcion():
    # Mascotas que aún no han sido adoptadas; las destacadas primero
    try:
        mascotas_db = (Mascota.query.filter_by(is_adopted=False)
                       .order_by(Mascota.destacada.desc(), Mascota.id.desc()).all())
    except Exception:
        app.logger.exception("No se pudieron cargar las mascotas")
        mascotas_db = []
    ubicaciones = sorted({m.ubicacion for m in mascotas_db if m.ubicacion})
    return render_template("main/Pagina1_Adopcion.html", mascotas=mascotas_db, ubicaciones=ubicaciones)


@app.route("/mascota/<int:mid>")
def Detalle_Mascota(mid):
    return render_template("main/Detalle_Mascota.html", mascota=db.get_or_404(Mascota, mid))


@app.route("/fundaciones")
def Pagina_Fundacion():
    return render_template("main/Pagina_Fundacion.html")


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------

@app.route("/registro", methods=["GET", "POST"])
def Registro_Usuario():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password")
        nombre = (request.form.get("nombre") or "").strip()
        next_url = safe_next_url(request.form.get("next") or request.args.get("next"), default="")

        if not all([email, password, nombre]):
            flash("Todos los campos son obligatorios", "error")
            return render_template("main/Registro_Usuario.html")

        if usuario.query.filter((usuario.email == email) | (usuario.username == nombre)).first():
            flash("Ese usuario o email ya está registrado", "error")
            return render_template("main/Registro_Usuario.html")

        u = usuario(username=nombre, email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.flush()  # obtener u.id para el historial
        registrar(u.id, "registro", "Creaste tu cuenta en Adopt Me", commit=False)
        db.session.commit()

        flash("¡Registro exitoso! Ahora puedes iniciar sesión", "success")
        return redirect(url_for("Iniciar_Sesion", next=next_url or None))

    return render_template("main/Registro_Usuario.html")


@app.route("/iniciar-sesion", methods=["GET", "POST"])
def Iniciar_Sesion():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        next_url = safe_next_url(request.form.get("next") or request.args.get("next"), default="")

        if not email or not password:
            flash("Email y contraseña son obligatorios", "error")
            return render_template("main/Iniciar_Sesion.html")

        if login_bloqueado(email):
            flash("Demasiados intentos fallidos. Espera 15 minutos e inténtalo de nuevo.", "error")
            return render_template("main/Iniciar_Sesion.html"), 429

        # Primero se busca en administradores y luego en usuarios normales
        admin_user = AdminModel.query.filter((AdminModel.email == email) | (AdminModel.username == email)).first()
        if admin_user and admin_user.active and admin_user.check_password(password):
            limpiar_fallos_login(email)
            session.clear()
            session["user_id"] = admin_user.id
            session["user_email"] = admin_user.email
            session["user_name"] = admin_user.username
            session["is_admin"] = True
            flash(f"¡Bienvenido, {admin_user.username} (admin)!", "success")
            return redirect(next_url or "/postularADM")

        user = usuario.query.filter((usuario.email == email) | (usuario.username == email)).first()
        if user and user.check_password(password):
            limpiar_fallos_login(email)
            session.clear()
            session["user_id"] = user.id
            session["user_email"] = user.email
            session["user_name"] = user.username
            registrar(user.id, "inicio_sesion", "Iniciaste sesión")
            flash(f"¡Bienvenido, {user.username}!", "success")
            return redirect(next_url or "/")

        registrar_fallo_login(email)
        flash("Email o contraseña incorrectos", "error")

    return render_template("main/Iniciar_Sesion.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente", "info")
    return redirect("/")


# El formulario envía los datos por fetch a /api/admin/admins (requiere código de registro)
@app.route("/registro-administrador")
def Registro_Administrador():
    return render_template("main/Registro_Administrador.html")


# ---------------------------------------------------------------------------
# Adopción
# ---------------------------------------------------------------------------

@app.route("/formulario", methods=["GET", "POST"])
@login_required
def Formulario_Para_Adoptar():
    if request.method == "GET":
        # Datos de la mascota elegida para mostrarla en el encabezado del formulario
        mascota_id = request.args.get("mascota", type=int)
        pet_name = request.args.get("pet")
        mascota = db.session.get(Mascota, mascota_id) if mascota_id else None
        if mascota:
            pet = {"nombre": mascota.nombre, "imagen": mascota.imagen_url}
        else:
            pet = {"nombre": pet_name, "imagen": None} if pet_name else None
        return render_template("main/Formulario_Para_Adoptar.html", pet=pet)

    nombre = request.form.get("nombre") or request.form.get("username")
    email = request.form.get("email")
    # La mascota llega por id (?mascota=ID) desde su ficha, o solo por nombre (?pet=Nombre)
    pet_name = request.args.get("pet") or request.form.get("pet_name")
    mascota_id = request.form.get("mascota_id", type=int) or request.args.get("mascota", type=int)
    mascota = db.session.get(Mascota, mascota_id) if mascota_id else None
    if not mascota and pet_name:
        mascota = Mascota.query.filter_by(nombre=pet_name, is_adopted=False).first()

    error = None
    if not nombre or not email:
        error = ("Nombre y email son obligatorios", 400)
    elif mascota and mascota.is_adopted:
        error = ("Esta mascota ya fue adoptada", 409)
    if error:
        msg, status = error
        if _wants_json():
            return jsonify({"ok": False, "msg": msg}), status
        flash(msg, "error")
        return redirect("/formulario")

    solicitud = adoptar_mascotas(
        mascota=mascota,
        username=nombre,
        email=email,
        telefono=request.form.get("telefono"),
        direccion=request.form.get("direccion"),
        ocupacion=request.form.get("ocupacion"),
        vivienda=request.form.get("vivienda"),
        tiene_mascotas=request.form.get("mascotas"),
        motivo=request.form.get("motivo"),
        pet_name=mascota.nombre if mascota else pet_name,
    )
    # Enlazar la solicitud con el usuario que la envía (los admins no están en 'usuarios')
    if not session.get("is_admin") and db.session.get(usuario, session["user_id"]):
        solicitud.adopter_id = session["user_id"]

    try:
        db.session.add(solicitud)
        if solicitud.adopter_id:
            registrar(
                solicitud.adopter_id, "solicitud_enviada",
                f"Enviaste una solicitud para adoptar a {solicitud.pet_name or 'una mascota'}",
                enlace=url_for("Detalle_Mascota", mid=mascota.id) if mascota else None, commit=False,
            )
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Error al guardar la solicitud de adopción")
        msg = "Ocurrió un error al guardar la solicitud. Intenta de nuevo más tarde."
        if _wants_json():
            return jsonify({"ok": False, "msg": msg}), 500
        flash(msg, "error")
        return redirect("/adopcion")

    if _wants_json():
        return jsonify({"ok": True, "msg": "Solicitud de adopción guardada"}), 201
    flash("¡Solicitud de adopción enviada correctamente! Te contactaremos pronto.", "success")
    return redirect("/adopcion")


# ---------------------------------------------------------------------------
# Publicación de mascotas
# ---------------------------------------------------------------------------

# Panel del administrador: publicar mascotas y gestionar solicitudes y postulaciones
@app.route("/postularADM", methods=["GET", "POST"])
@admin_required
def Postular_Admin():
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        if not nombre or not descripcion:
            flash("El nombre y la descripción son obligatorios", "error")
            return redirect(url_for("Postular_Admin"))
        imagen = save_uploaded_image(request.files.get("imagen"))
        try:
            db.session.add(Mascota(
                nombre=nombre,
                descripcion=descripcion,
                imagen=imagen,
                autor=session["user_name"],
                publicado_por_id=session["user_id"],
                destacada=bool(request.form.get("destacada")),
                **{c: request.form.get(c) or None for c in Mascota.CAMPOS},
            ))
            db.session.commit()
            flash(f"¡{nombre} ya aparece en el catálogo de adopción!", "success")
        except Exception:
            db.session.rollback()
            app.logger.exception("Error al publicar la mascota")
            flash("No se pudo publicar la mascota", "error")
        return redirect(url_for("Postular_Admin"))

    mascotas_db = Mascota.query.order_by(Mascota.destacada.desc(), Mascota.id.desc()).all()
    solicitudes = adoptar_mascotas.query.order_by(adoptar_mascotas.is_confirmed, adoptar_mascotas.id.desc()).all()
    postulaciones = PostularMascotas.query.order_by(PostularMascotas.id.desc()).all()
    return render_template(
        "main/postularADM.html",
        mascotas=mascotas_db,
        solicitudes=solicitudes,
        postulaciones=postulaciones,
        usuarios=_resumen_usuarios(),
        admins=AdminModel.query.order_by(AdminModel.active.desc(), AdminModel.username).all(),
    )


def _resumen_usuarios():
    """Usuarios con sus totales y su última actividad (tres consultas agregadas, sin N+1)."""
    def por_usuario(columna, agregado):
        return dict(db.session.query(columna, agregado).filter(columna.isnot(None)).group_by(columna).all())

    solicitudes = por_usuario(adoptar_mascotas.adopter_id, func.count(adoptar_mascotas.id))
    postulaciones = por_usuario(PostularMascotas.usuario_id, func.count(PostularMascotas.id))
    ultima = por_usuario(Actividad.usuario_id, func.max(Actividad.created_at))
    return [
        {
            "u": u,
            "solicitudes": solicitudes.get(u.id, 0),
            "postulaciones": postulaciones.get(u.id, 0),
            "ultima_actividad": ultima.get(u.id),
        }
        for u in usuario.query.order_by(usuario.created_at.desc(), usuario.id.desc()).all()
    ]


# Ficha de un usuario para la fundación: datos, solicitudes, postulaciones y actividad
@app.route("/postularADM/usuarios/<int:uid>")
@admin_required
def Admin_Usuario(uid):
    u = db.get_or_404(usuario, uid)
    actividades = (Actividad.query.filter_by(usuario_id=u.id)
                   .order_by(Actividad.created_at.desc(), Actividad.id.desc()).limit(100).all())
    return render_template(
        "main/Admin_Usuario.html",
        u=u,
        grupos=agrupar_por_dia(actividades),
        solicitudes=sorted(u.solicitudes, key=lambda s: s.id, reverse=True),
        postulaciones=sorted(u.postulaciones, key=lambda p: p.id, reverse=True),
    )


# Formulario para que un usuario proponga una mascota en adopción
@app.route("/postular", methods=["GET", "POST"])
@login_required
def Postular_Mascotas():
    if request.method == "POST":
        p = PostularMascotas(
            nombre=request.form.get("nombre"),
            especie=request.form.get("especie"),
            raza=request.form.get("raza"),
            edad=request.form.get("edad"),
            sexo=request.form.get("sexo"),
            # El campo en la plantilla se llama "tamaño" (con tilde); se guarda en la columna 'tamanio'
            tamanio=request.form.get("tamaño") or request.form.get("tamano") or request.form.get("tamanio"),
            color=request.form.get("color"),
            ubicacion=request.form.get("ubicacion"),
            imagen=save_uploaded_image(request.files.get("imagen")),
            # Los admins no están en 'usuarios'; su postulación queda sin usuario asociado
            usuario_id=None if session.get("is_admin") else session["user_id"],
        )
        try:
            db.session.add(p)
            registrar(p.usuario_id, "postulacion_enviada",
                      f"Postulaste a {p.nombre or 'una mascota'} para darla en adopción", commit=False)
            db.session.commit()
            flash("¡Gracias! Revisaremos la información de la mascota.", "success")
        except Exception:
            db.session.rollback()
            app.logger.exception("Error al guardar la postulación")
            flash("No se pudo guardar la postulación", "error")
        return redirect("/adopcion")

    return render_template("main/Postular_Mascotas.html")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5100")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
