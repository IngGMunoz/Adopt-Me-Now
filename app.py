from flask import (
    Flask, # Importar Flask
    request, # Para manejar solicitudes HTTP
    jsonify, # Para respuestas JSON
    redirect, # Para redireccionar a otras rutas
    render_template, # Para renderizar plantillas HTML
    url_for, # Para construir URLs
    session, # Manejo de sesiones
    flash, # Para mensajes flash (notificaciones)
)
from Config.db import app, db
from sqlalchemy import inspect, text

# importar blueprints de controllers
from Config.controller.Mascotascontroller import routes_MascotasC
from Config.controller.Usercontroller import routes_UserC
from Config.controller.PostularMascontroller import routes_PostularC
from Config.controller.adoptar_mascontroller import Routes_adoptarC
from Config.controller.Admincontroller import Routes_adminC

# registrar blueprints
app.register_blueprint(routes_MascotasC)
app.register_blueprint(routes_UserC)
app.register_blueprint(routes_PostularC)
app.register_blueprint(Routes_adoptarC)
app.register_blueprint(Routes_adminC)


# Lista global para mascotas subidas por el admin
mascotas = []
from functools import wraps
import hashlib
from Models.mascotas import Mascota
from Models.postular_mascotas import PostularMascotas
from Models.admins import admin as AdminModel
from Models.adoptar_mascotas import adoptar_mascotas  # Usaremos esta tabla migrada para las solicitudes

# Configurar clave secreta para sesiones
app.secret_key = "adopt-me-secret-key-2025"  # En producción, usar variable de entorno

# Nota: reemplazamos el almacenamiento temporal por el modelo en la DB.
from Models.usuario import usuario
users_db = {}  # mantenemos la variable por compatibilidad con código antiguo pero no se usa para auth


# Asegurar que la tabla adoptar_mascotas tenga las columnas esperadas por el formulario
def ensure_adoptar_mascotas_schema():
    insp = inspect(db.engine)
    if not insp.has_table("adoptar_mascotas"):
        db.create_all()
        return

    # Paso 1: columnas requeridas
    cols_list = insp.get_columns("adoptar_mascotas")
    cols = {c["name"] for c in cols_list}
    required = [
        ("telefono", "VARCHAR(30) NULL"),
        ("direccion", "VARCHAR(200) NULL"),
        ("ocupacion", "VARCHAR(100) NULL"),
        ("vivienda", "VARCHAR(80) NULL"),
        ("tiene_mascotas", "VARCHAR(80) NULL"),
        ("motivo", "TEXT NULL"),
        ("pet_name", "VARCHAR(120) NULL"),
        ("adopter_id", "INT NULL"),
        ("is_confirmed", "TINYINT(1) NOT NULL DEFAULT 0"),
    ]
    for name, ddl in required:
        if name not in cols:
            try:
                db.session.execute(text(f"ALTER TABLE adoptar_mascotas ADD COLUMN {name} {ddl}"))
                db.session.commit()
            except Exception:
                db.session.rollback()

    # Paso 2: índice adopter_id
    cols_list = insp.get_columns("adoptar_mascotas")
    cols = {c["name"] for c in cols_list}
    if "adopter_id" in cols:
        try:
            idx = db.session.execute(text(
                """
                SELECT COUNT(1) AS n
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = 'adoptar_mascotas'
                  AND index_name = 'idx_adoptar_adopter_id'
                """
            )).scalar()
            if not idx:
                db.session.execute(text("CREATE INDEX idx_adoptar_adopter_id ON adoptar_mascotas(adopter_id)"))
                db.session.commit()
        except Exception:
            db.session.rollback()

    # Paso 3: FK adopter_id -> usuarios.id
    try:
        if insp.has_table("usuarios") and "adopter_id" in cols:
            fk_exists = db.session.execute(text(
                """
                SELECT COUNT(1) AS n
                FROM information_schema.REFERENTIAL_CONSTRAINTS
                WHERE CONSTRAINT_SCHEMA = DATABASE()
                  AND CONSTRAINT_NAME = 'fk_adoptar_usuarios'
                """
            )).scalar()
            if not fk_exists:
                try:
                    db.session.execute(text(
                        "ALTER TABLE adoptar_mascotas ADD CONSTRAINT fk_adoptar_usuarios "
                        "FOREIGN KEY (adopter_id) REFERENCES usuarios(id) "
                        "ON UPDATE CASCADE ON DELETE SET NULL"
                    ))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
    except Exception:
        db.session.rollback()

    # Paso 4: Relajar password_hash NOT NULL
    try:
        meta = {c["name"]: c for c in cols_list}
        ph = meta.get("password_hash")
        if ph and not ph.get("nullable", True):
            try:
                db.session.execute(text(
                    "ALTER TABLE adoptar_mascotas MODIFY COLUMN password_hash VARCHAR(256) NULL"
                ))
                db.session.commit()
            except Exception:
                db.session.rollback()
    except Exception:
        db.session.rollback()

    # Paso 5: Defaults de timestamps si existen sin default
    try:
        cols_now = {c["name"] for c in insp.get_columns("adoptar_mascotas")}
        if "created_at" in cols_now:
            try:
                db.session.execute(text(
                    "ALTER TABLE adoptar_mascotas MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ))
                db.session.commit()
            except Exception:
                db.session.rollback()
        if "updated_at" in cols_now:
            try:
                db.session.execute(text(
                    "ALTER TABLE adoptar_mascotas MODIFY COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                ))
                db.session.commit()
            except Exception:
                db.session.rollback()
    except Exception:
        db.session.rollback()

    # Paso 6: Asegurar que 'username' NO tenga índice UNIQUE accidental
    try:
        rows = db.session.execute(text(
            """
            SELECT index_name, non_unique
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'adoptar_mascotas'
              AND column_name = 'username'
            """
        )).fetchall()
        # Eliminar cualquier índice único sobre username
        for idx_name, non_unique in rows:
            try:
                if int(non_unique) == 0:
                    db.session.execute(text(f"ALTER TABLE adoptar_mascotas DROP INDEX `{idx_name}`"))
                    db.session.commit()
            except Exception:
                db.session.rollback()

        # Si después de eliminar no queda ningún índice, crear uno normal (no único)
        remaining = db.session.execute(text(
            """
            SELECT COUNT(1)
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'adoptar_mascotas'
              AND column_name = 'username'
            """
        )).scalar() or 0
        if int(remaining) == 0:
            try:
                db.session.execute(text("CREATE INDEX idx_adoptar_username ON adoptar_mascotas(username)"))
                db.session.commit()
            except Exception:
                db.session.rollback()
    except Exception:
        db.session.rollback()


# Ejecutar la verificación de esquema al iniciar la app
with app.app_context():
    ensure_adoptar_mascotas_schema()


# Endpoint utilitario (desarrollo) para forzar la migración de la tabla adoptar_mascotas
@app.route("/_setup/migrate-adoptar", methods=["POST", "GET"])
def migrate_adoptar_table():
    try:
        ensure_adoptar_mascotas_schema()
        return jsonify({"ok": True, "msg": "Esquema de adoptar_mascotas verificado/ajustado"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


# Decorador para rutas que requieren autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión para acceder a esta página", "error")
            return redirect(url_for("Iniciar_Sesion"))
        return f(*args, **kwargs)

    return decorated_function


# Función helper para verificar si el usuario está autenticado
def is_authenticated():
    return "user_id" in session


# Función helper para obtener el usuario actual
def get_current_user():
    if "user_id" in session:
        try:
            # si es admin, los datos están en la sesión
            if session.get("is_admin"):
                return {"id": session.get("user_id"), "email": session.get("user_email"), "nombre": session.get("user_name"), "is_admin": True}
            u = usuario.query.get(session["user_id"])
            if not u:
                return None
            # devolver un dict ligero similar al antiguo esquema usado en plantillas
            return {"id": u.id, "email": u.email, "nombre": u.username}
        except Exception:
            return None
    return None


# Context processor para hacer disponible la información de autenticación en todas las plantillas
@app.context_processor
def inject_auth():
    return {"is_authenticated": is_authenticated(), "current_user": get_current_user()}


# Página de detalle de cachorro
@app.route("/cachorro")
def Pagina2_Cachorro():
    return render_template("main/Pagina2_Cachorro.html")


# Página de detalle de Michi
@app.route("/michi")
def Pagina_Michi():
    return render_template("main/Pagina_Michi.html")


# Página de detalle de Rocky (perro 2)
@app.route("/rocky")
def Pagina_perro2():
    return render_template("main/Pagina_perro2.html")


# Formulario de adopción (requiere autenticación)
@app.route("/formulario", methods=["GET", "POST"])
@login_required
def Formulario_Para_Adoptar():
    if request.method == "POST":
        # Procesar solicitud de adopción con usuario autenticado y persistir en la tabla adoptar_mascotas
        user = get_current_user()

        nombre = request.form.get("nombre") or request.form.get("username") or None
        email = request.form.get("email") or None
        telefono = request.form.get("telefono") or None
        direccion = request.form.get("direccion") or None
        ocupacion = request.form.get("ocupacion") or None
        vivienda = request.form.get("vivienda") or None
        tiene_mascotas = request.form.get("mascotas") or None
        motivo = request.form.get("motivo") or None

        # El nombre de la mascota puede venir como parámetro en la URL (?pet=Nombre) o como campo
        pet_name = request.args.get("pet") or request.form.get("pet_name") or None

        # Log de depuración de los valores recibidos
        print("[DEBUG][/formulario] Datos recibidos:")
        print({
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "direccion": direccion,
            "ocupacion": ocupacion,
            "vivienda": vivienda,
            "tiene_mascotas(form campo 'mascotas')": tiene_mascotas,
            "motivo": motivo,
            "pet_name": pet_name,
            "user_id_session": session.get("user_id"),
        })

        # Validación mínima antes de crear el objeto (evita INSERT con nulos inesperados)
        if not nombre or not email:
            msg = "Nombre y email son obligatorios";
            print("[ERROR][/formulario]", msg)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "msg": msg}), 400
            flash(msg, "error")
            return redirect("/formulario")

        # Crear registro en la tabla adoptar_mascotas (ya migrada con columnas nuevas)
        a = adoptar_mascotas(
            username=nombre,
            email=email,
            telefono=telefono,
            direccion=direccion,
            ocupacion=ocupacion,
            vivienda=vivienda,
            tiene_mascotas=tiene_mascotas,
            motivo=motivo,
            pet_name=pet_name,
        )

        # Si el usuario está autenticado y tenemos user_id, enlazamos adopter_id
        try:
            # Solo enlazar adopter_id si es un usuario normal existente en 'usuarios'
            if session.get("user_id") and not session.get("is_admin"):
                try:
                    uobj = usuario.query.get(session.get("user_id"))
                except Exception:
                    uobj = None
                if uobj:
                    a.adopter_id = uobj.id
                else:
                    print("[WARN][/formulario] user_id en sesión no encontrado en 'usuarios'; guardando sin FK")

            db.session.add(a)
            db.session.commit()
            print(f"[DEBUG][/formulario] Solicitud guardada en adoptar_mascotas id={a.id}")
            # Si la solicitud viene por AJAX/Fetch, devolver JSON para que el frontend pueda manejarlo
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.accept_json:
                return jsonify({"ok": True, "msg": "Solicitud de adopción guardada"}), 201

            flash("¡Solicitud de adopción enviada correctamente! Te contactaremos pronto.", "success")
        except Exception as e:
            db.session.rollback()
            # Imprimir el error en la consola del servidor para depuración
            import traceback
            print("--- ERROR AL GUARDAR ADOPCIÓN ---")
            traceback.print_exc()
            print("---------------------------------")
            # registrar/mostrar un mensaje genérico
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.accept_json:
                return jsonify({"ok": False, "msg": f"Ocurrió un error al guardar la solicitud: {e}"}), 500
            flash("Ocurrió un error al guardar la solicitud. Intenta de nuevo más tarde.", "error")
        return redirect("/adopcion")
    return render_template("main/Formulario_Para_Adoptar.html")


# Home
@app.route("/")
def Pagina_Principal():
    return render_template("main/Pagina_Principal.html")


# Registro usuario
@app.route("/registro", methods=["GET", "POST"])
def Registro_Usuario():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        nombre = request.form.get("nombre")
        telefono = request.form.get("telefono")

        # Preserve next param so user can be sent back after login
        next_url = request.form.get("next") or request.args.get("next") or None

        # Validar que todos los campos estén presentes
        if not all([email, password, nombre]):
            flash("Todos los campos son obligatorios", "error")
            return render_template("main/Registro_Usuario.html")

        # Verificar si el usuario ya existe en la base de datos
        if usuario.query.filter_by(email=email).first():
            flash("Este email ya está registrado", "error")
            return render_template("main/Registro_Usuario.html")

        # Crear nuevo usuario en la base de datos
        username = nombre if nombre else email.split("@")[0]
        u = usuario(username=username, email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

        flash("¡Registro exitoso! Ahora puedes iniciar sesión", "success")
        if next_url:
            try:
                if isinstance(next_url, str) and next_url.startswith("/"):
                    return redirect(url_for("Iniciar_Sesion") + "?next=" + next_url)
            except Exception:
                pass
        return redirect("/iniciar-sesion")

    return render_template("main/Registro_Usuario.html")


@app.route("/iniciar-sesion", methods=["GET", "POST"])
def Iniciar_Sesion():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Intento de next param para redirigir al origen tras login
        next_url = request.form.get("next") or request.args.get("next") or "/"

        # Validar campos
        if not email or not password:
            flash("Email y contraseña son obligatorios", "error")
            return render_template("main/Iniciar_Sesion.html")

        # Primero intentar buscar en admins
        admin_user = AdminModel.query.filter((AdminModel.email == email) | (AdminModel.username == email)).first()
        if admin_user and admin_user.check_password(password):
            session["user_id"] = admin_user.id
            session["user_email"] = admin_user.email
            session["user_name"] = admin_user.username
            session["is_admin"] = True
            session["role"] = admin_user.role

            flash(f'¡Bienvenido, {admin_user.username} (admin)!', "success")
            try:
                # redirigir al panel de admin si no viene next
                if isinstance(next_url, str) and next_url.startswith("/") and next_url != "/":
                    return redirect(next_url)
            except Exception:
                pass
            return redirect("/postularADM")

        # Si no es admin, intentar usuario normal
        user = usuario.query.filter((usuario.email == email) | (usuario.username == email)).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_email"] = user.email
            session["user_name"] = user.username
            session.pop("is_admin", None)
            session.pop("role", None)

            flash(f'¡Bienvenido, {user.username}!', "success")
            try:
                if isinstance(next_url, str) and next_url.startswith("/"):
                    return redirect(next_url)
            except Exception:
                pass
            return redirect("/")

        # si todo falla
        flash("Email o contraseña incorrectos", "error")

    return render_template("main/Iniciar_Sesion.html")


# Ruta para cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente", "info")
    return redirect("/")


# Registro administrador
@app.route("/registro-administrador", methods=["GET", "POST"])
def Registro_Administrador():
    if request.method == "POST":
        # Aquí podrías validar/guardar datos de administrador
        return render_template("main/postularADM.html")
    return render_template("main/Registro_Administrador.html")


# postular Mascotas (ADMIN)
@app.route("/postularADM", methods=["GET", "POST"])
def Postular_Admin():
    from werkzeug.utils import secure_filename
    import os
    if request.method == "POST":
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        imagen = request.files.get("imagen")
        autor = session.get("user_name", "Anónimo")

        # Guardar la imagen en static/uploads/
        uploads_dir = os.path.join(app.root_path, "static", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        imagen_filename = ""
        if imagen and imagen.filename:
            import uuid
            safe_name = secure_filename(imagen.filename)
            imagen_filename = f"{uuid.uuid4().hex}_{safe_name}"
            imagen.save(os.path.join(uploads_dir, imagen_filename))

        # Crear y persistir Mascota en la base de datos para que aparezca en /adopcion
        try:
            m = Mascota(nombre=nombre or "Sin nombre", descripcion=descripcion or "", imagen=imagen_filename, autor=autor)
            db.session.add(m)
            db.session.commit()
        except Exception:
            db.session.rollback()
            # fallback: mantener la lista en memoria si la BD falla
            mascotas.append({"nombre": nombre, "descripcion": descripcion, "imagen": imagen_filename, "autor": autor})

        return redirect("/adopcion")

    # obtener mascotas desde la BD para mostrarlas en la página del admin
    try:
        mascotas_db = Mascota.query.order_by(Mascota.id.desc()).all()
    except Exception:
        mascotas_db = mascotas
    return render_template("main/postularADM.html", mascotas=mascotas_db)


# Listado de adopción / Mascotas
@app.route("/adopcion")
def Pagina_Adopcion():
    # Mostrar mascotas persistidas en la base de datos (no adoptadas)
    try:
        mascotas_db = Mascota.query.filter_by(is_adopted=False).order_by(Mascota.id.desc()).all()
    except Exception:
        # fallback a la lista en memoria si hay error con la BD
        mascotas_db = mascotas
    return render_template("main/Pagina1_Adopcion.html", mascotas=mascotas_db)


# Alias para compatibilidad: /mascotas -> /adopcion
@app.route("/mascotas")
def Mascotas_Alias():
    return redirect("/adopcion")


# Fundaciones
@app.route("/fundaciones")
def Pagina_Fundacion():
    return render_template("main/Pagina_Fundacion.html")


# Página específica de la fundación Funcuan
@app.route("/funcuan")
def Pagina_Funcuan():
    # reutilizamos la plantilla de fundación por ahora; si luego hay varias, podemos parametrizar
    return render_template("main/Pagina_Fundacion.html")


# Página para postular mascotas
@app.route("/postular", methods=["GET", "POST"])
def Postular_Mascotas():
    if request.method == "POST":
        # Procesar formulario y guardar en la tabla postular_mascotas
        from werkzeug.utils import secure_filename
        import os

        nombre = request.form.get("nombre")
        especie = request.form.get("especie")
        raza = request.form.get("raza")
        edad = request.form.get("edad")
        sexo = request.form.get("sexo")
        # El campo en la plantilla se llama "tamaño" (con tilde). Lo leemos y lo guardamos en la columna 'tamanio'
        tamanio = request.form.get("tamaño") or request.form.get("tamano") or request.form.get("tamanio")
        color = request.form.get("color")
        ubicacion = request.form.get("ubicacion")
        file = request.files.get("imagen")

        imagen_filename = ""
        if file and file.filename:
            uploads_dir = os.path.join(app.root_path, "static", "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            imagen_filename = secure_filename(file.filename)
            file.save(os.path.join(uploads_dir, imagen_filename))

        p = PostularMascotas(
            nombre=nombre,
            especie=especie,
            raza=raza,
            edad=edad,
            sexo=sexo,
            tamanio=tamanio,
            color=color,
            ubicacion=ubicacion,
            imagen=imagen_filename,
        )
        try:
            db.session.add(p)
            db.session.commit()
            # opcional: flash
        except Exception:
            db.session.rollback()
        return redirect("/adopcion")

    return render_template("main/Postular_Mascotas.html")


if __name__ == "__main__":
    app.run(debug=True, port=5100, host="0.0.0.0")