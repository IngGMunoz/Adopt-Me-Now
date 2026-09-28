import os
from datetime import date

from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for

from Config.db import app, db
from Config.auth import (
    admin_required,
    is_authenticated,
    login_required,
    safe_next_url,
    save_uploaded_image,
)
from Config.schema import init_db
from Config.catalogo import MASCOTAS_DESTACADAS
from Config.actividad import registrar
import Config.filtros  # noqa: F401  (filtros de fecha para las plantillas)

# Modelos
from Models.mascotas import Mascota
from Models.postular_mascotas import PostularMascotas
from Models.admins import admin as AdminModel
from Models.adoptar_mascotas import adoptar_mascotas
from Models.usuario import usuario
from Models.actividad import Actividad  # noqa: F401

# Blueprints (API)
from Config.controller.Mascotascontroller import routes_MascotasC
from Config.controller.Usercontroller import routes_UserC
from Config.controller.PostularMascontroller import routes_PostularC
from Config.controller.adoptar_mascontroller import Routes_adoptarC
from Config.controller.Admincontroller import Routes_adminC
from Config.controller.Cuentacontroller import routes_CuentaC

app.register_blueprint(routes_MascotasC)
app.register_blueprint(routes_UserC)
app.register_blueprint(routes_PostularC)
app.register_blueprint(Routes_adoptarC)
app.register_blueprint(Routes_adminC)
app.register_blueprint(routes_CuentaC)

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


def _enlace_mascota(nombre):
    """Perfil de una mascota destacada a partir de su nombre, si tiene uno."""
    slug = next((s for s, m in MASCOTAS_DESTACADAS.items() if m["nombre"] == nombre), None)
    return url_for("Detalle_Mascota", slug=slug) if slug else None


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
    # Últimas mascotas publicadas para la sección "Recién llegados"
    try:
        recientes = Mascota.query.filter_by(is_adopted=False).order_by(Mascota.id.desc()).limit(3).all()
        total = Mascota.query.filter_by(is_adopted=False).count() + len(MASCOTAS_DESTACADAS)
        adoptadas = Mascota.query.filter_by(is_adopted=True).count()
    except Exception:
        app.logger.exception("No se pudieron cargar las mascotas")
        recientes, total, adoptadas = [], len(MASCOTAS_DESTACADAS), 0
    return render_template(
        "main/Pagina_Principal.html",
        recientes=recientes,
        destacadas=MASCOTAS_DESTACADAS,
        total_disponibles=total,
        total_adoptadas=adoptadas,
    )


@app.route("/adopcion")
def Pagina_Adopcion():
    # Mascotas publicadas por los administradores que aún no han sido adoptadas
    try:
        mascotas_db = Mascota.query.filter_by(is_adopted=False).order_by(Mascota.id.desc()).all()
    except Exception:
        app.logger.exception("No se pudieron cargar las mascotas")
        mascotas_db = []
    return render_template("main/Pagina1_Adopcion.html", mascotas=mascotas_db, destacadas=MASCOTAS_DESTACADAS)


# Alias para compatibilidad: /mascotas -> /adopcion
@app.route("/mascotas")
def Mascotas_Alias():
    return redirect("/adopcion")


# Perfil de las mascotas destacadas: /cachorro, /michi, /rocky
@app.route("/cachorro", defaults={"slug": "cachorro"})
@app.route("/michi", defaults={"slug": "michi"})
@app.route("/rocky", defaults={"slug": "rocky"})
def Detalle_Mascota(slug):
    mascota = MASCOTAS_DESTACADAS.get(slug)
    if not mascota:
        abort(404)
    return render_template("main/Detalle_Mascota.html", mascota=mascota, slug=slug)


@app.route("/fundaciones")
def Pagina_Fundacion():
    return render_template("main/Pagina_Fundacion.html")


# Página de la fundación Funcuan (reutiliza la plantilla de fundaciones)
@app.route("/funcuan")
def Pagina_Funcuan():
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

        # Primero se busca en administradores y luego en usuarios normales
        admin_user = AdminModel.query.filter((AdminModel.email == email) | (AdminModel.username == email)).first()
        if admin_user and admin_user.active and admin_user.check_password(password):
            session.clear()
            session["user_id"] = admin_user.id
            session["user_email"] = admin_user.email
            session["user_name"] = admin_user.username
            session["is_admin"] = True
            session["role"] = admin_user.role
            flash(f"¡Bienvenido, {admin_user.username} (admin)!", "success")
            return redirect(next_url or "/postularADM")

        user = usuario.query.filter((usuario.email == email) | (usuario.username == email)).first()
        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["user_email"] = user.email
            session["user_name"] = user.username
            registrar(user.id, "inicio_sesion", "Iniciaste sesión")
            flash(f"¡Bienvenido, {user.username}!", "success")
            return redirect(next_url or "/")

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
        pet = None
        mascota_id = request.args.get("mascota", type=int)
        pet_name = request.args.get("pet")
        mascota = db.session.get(Mascota, mascota_id) if mascota_id else None
        if mascota:
            imagen = url_for("static", filename="uploads/" + mascota.imagen) if mascota.imagen else None
            pet = {"nombre": mascota.nombre, "imagen": imagen}
        elif pet_name:
            destacada = next((m for m in MASCOTAS_DESTACADAS.values() if m["nombre"] == pet_name), None)
            imagen = url_for("static", filename=destacada["imagen"]) if destacada else None
            pet = {"nombre": pet_name, "imagen": imagen}
        return render_template("main/Formulario_Para_Adoptar.html", pet=pet)

    nombre = request.form.get("nombre") or request.form.get("username")
    email = request.form.get("email")
    # La mascota llega por id (?mascota=ID) desde el catálogo, o solo por nombre (?pet=Nombre)
    # desde las páginas fijas como /michi, que no están en la tabla mascotas.
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
                enlace=_enlace_mascota(solicitud.pet_name), commit=False,
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
            ))
            db.session.commit()
            flash(f"¡{nombre} ya aparece en el catálogo de adopción!", "success")
        except Exception:
            db.session.rollback()
            app.logger.exception("Error al publicar la mascota")
            flash("No se pudo publicar la mascota", "error")
        return redirect(url_for("Postular_Admin"))

    mascotas_db = Mascota.query.order_by(Mascota.id.desc()).all()
    solicitudes = adoptar_mascotas.query.order_by(adoptar_mascotas.is_confirmed, adoptar_mascotas.id.desc()).all()
    postulaciones = PostularMascotas.query.order_by(PostularMascotas.id.desc()).all()
    return render_template(
        "main/postularADM.html",
        mascotas=mascotas_db,
        solicitudes=solicitudes,
        postulaciones=postulaciones,
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
