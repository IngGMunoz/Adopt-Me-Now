from flask import (
    Flask,
    request,
    jsonify,
    redirect,
    render_template,
    url_for,
    session,
    flash,
)
from Config.db import app
from functools import wraps
import hashlib

# Configurar clave secreta para sesiones
app.secret_key = "adopt-me-secret-key-2025"  # En producción, usar variable de entorno

# Almacenamiento temporal de usuarios (en producción usar base de datos)
users_db = {}


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
        return users_db.get(session["user_id"])
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
        # Procesar solicitud de adopción con usuario autenticado
        user = get_current_user()
        pet_name = request.form.get("pet_name", "Mascota")

        flash(
            f"¡Solicitud de adopción enviada correctamente para {pet_name}! Te contactaremos pronto.",
            "success",
        )
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
        next_url = request.form.get('next') or request.args.get('next') or None

        # Validar que todos los campos estén presentes
        if not all([email, password, nombre]):
            flash("Todos los campos son obligatorios", "error")
            return render_template("main/Registro_Usuario.html")

        # Verificar si el usuario ya existe
        if email in [user["email"] for user in users_db.values()]:
            flash("Este email ya está registrado", "error")
            return render_template("main/Registro_Usuario.html")

        # Crear nuevo usuario
        user_id = len(users_db) + 1
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        users_db[user_id] = {
            "id": user_id,
            "email": email,
            "password": hashed_password,
            "nombre": nombre,
            "telefono": telefono or "",
            "registered_at": __import__("datetime").datetime.now(),
        }

        flash("¡Registro exitoso! Ahora puedes iniciar sesión", "success")
        if next_url:
            try:
                if isinstance(next_url, str) and next_url.startswith('/'):
                    return redirect(url_for('Iniciar_Sesion') + '?next=' + next_url)
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
        next_url = request.form.get('next') or request.args.get('next') or '/'

        # Validar campos
        if not email or not password:
            flash("Email y contraseña son obligatorios", "error")
            return render_template("main/Iniciar_Sesion.html")

        # Buscar usuario por email
        user = None
        for u in users_db.values():
            if u["email"] == email:
                user = u
                break

        # Validar credenciales
        if user and user["password"] == hashlib.sha256(password.encode()).hexdigest():
            # Iniciar sesión
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            session["user_name"] = user["nombre"]

            flash(f'¡Bienvenido, {user["nombre"]}!', "success")
            # Redirigir al next si es seguro (ruta interna)
            try:
                if isinstance(next_url, str) and next_url.startswith('/'):
                    return redirect(next_url)
            except Exception:
                pass
            return redirect("/")
        else:
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
    # Aquí va la lógica para manejar el formulario y mostrar las mascotas
    return render_template("main/postularADM.html")


# Listado de adopción / Mascotas
@app.route("/adopcion")
def Pagina_Adopcion():
    return render_template("main/Pagina1_Adopcion.html")


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
        # Aquí podrías procesar y guardar la postulación de mascota
        return redirect("/adopcion")
    return render_template("main/Postular_Mascotas.html")


if __name__ == "__main__":
    app.run(debug=True, port=5100, host="0.0.0.0")
