
from flask import Flask, request, jsonify, redirect, render_template, url_for, session, flash
from Config.db import app
from functools import wraps

# Configurar clave secreta para sesiones
app.secret_key = 'tu_clave_secreta_super_segura_cambiar_en_produccion'

# Decorador para requerir autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para postularte a adoptar una mascota.', 'warning')
            return redirect(url_for('Iniciar_Sesion'))
        return f(*args, **kwargs)
    return decorated_function

# Función auxiliar para verificar si el usuario está autenticado
def is_authenticated():
    return 'user_id' in session

# Página de detalle de cachorro
@app.route("/cachorro")
def Pagina2_Cachorro():
    return render_template("main/Pagina2_Cachorro.html")

# Formulario de adopción (REQUIERE AUTENTICACIÓN)
@app.route("/formulario", methods=["GET", "POST"])
@login_required
def Formulario_Para_Adoptar():
    if request.method == "POST":
        # Procesar solicitud de adopción con datos del usuario autenticado
        user_id = session.get('user_id')
        user_email = session.get('user_email', 'Usuario')
        
        # Aquí podrías guardar la solicitud en la base de datos
        # Por ahora, mostramos mensaje de éxito y redirigimos
        flash(f'¡Tu solicitud de adopción ha sido enviada exitosamente!', 'success')
        return redirect("/cachorro")
    
    # Pasar datos del usuario al formulario
    return render_template("main/Formulario_Para_Adoptar.html", 
                         user_authenticated=True,
                         user_email=session.get('user_email', ''),
                         user_name=session.get('user_name', ''))



# Context processor para hacer datos de sesión disponibles en todos los templates
@app.context_processor
def inject_user():
    return dict(
        user_authenticated=is_authenticated(),
        user_name=session.get('user_name', ''),
        user_email=session.get('user_email', '')
    )

# Home
@app.route("/")
def Pagina_Principal():
    return render_template("main/Pagina_Principal.html")


# Registro usuario
@app.route("/registro", methods=["GET", "POST"])
def Registro_Usuario():
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validaciones básicas
        if not nombre or not email or not password:
            flash('Todos los campos son obligatorios.', 'error')
            return render_template("main/Registro_Usuario.html")
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template("main/Registro_Usuario.html")
        
        # TODO: Aquí guardarías el usuario en la base de datos
        # Por ahora simulamos registro exitoso
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect("/iniciar-sesion")
    
    return render_template("main/Registro_Usuario.html")

@app.route("/iniciar-sesion", methods=["GET", "POST"])
def Iniciar_Sesion():
    if request.method == "POST":
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validaciones básicas
        if not email or not password:
            flash('Email y contraseña son obligatorios.', 'error')
            return render_template("main/Iniciar_Sesion.html")
        
        # TODO: Aquí validarías credenciales con la base de datos
        # Por ahora simulamos login exitoso para cualquier email válido
        if '@' in email and len(password) >= 3:
            # Crear sesión de usuario
            session['user_id'] = email  # Usar email como ID temporal
            session['user_email'] = email
            session['user_name'] = email.split('@')[0].capitalize()  # Nombre basado en email
            
            flash(f'¡Bienvenido/a {session["user_name"]}!', 'success')
            
            # Redirigir a donde el usuario quería ir originalmente
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect("/")
        else:
            flash('Credenciales inválidas. Intenta nuevamente.', 'error')
            return render_template("main/Iniciar_Sesion.html")
    
    return render_template("main/Iniciar_Sesion.html")

# Cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect("/")

# Registro administrador
@app.route("/registro-administrador", methods=["GET", "POST"])
def Registro_Administrador():
    if request.method == "POST":
        # Aquí podrías validar/guardar datos de administrador
        return redirect("/iniciar-sesion")
    return render_template("main/Registro_Administrador.html")

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
