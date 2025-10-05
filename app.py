
"""
ADOPT ME NOW - Sistema de Adopción de Mascotas
==============================================

Aplicación Flask para conectar mascotas en adopción con familias interesadas.
Implementa un sistema completo de autenticación, gestión de usuarios y 
formularios de adopción con arquitectura de componentes reutilizables.

Autor: Equipo Adopt Me Now
Versión: 1.0.0
Tecnologías: Flask, Jinja2, MySQL, HTML/CSS/JavaScript
"""

from flask import Flask, request, jsonify, redirect, render_template, url_for, session, flash
from Config.db import app  # Configuración de Flask y base de datos
from functools import wraps  # Para decoradores de autenticación
import hashlib  # Para hash de contraseñas (SHA-256)
from validation_utils import (  # Sistema de validación unificado
    validate_registration_data,
    validate_login_data, 
    validate_adoption_data,
    validation_error_response,
    FormValidator
)

# ====================================================================
# CONFIGURACIÓN DE SEGURIDAD
# ====================================================================

# Clave secreta para manejo seguro de sesiones Flask
# TODO: En producción, usar variable de entorno (os.environ.get('SECRET_KEY'))
app.secret_key = 'adopt-me-secret-key-2025'

# ====================================================================
# ALMACENAMIENTO DE DATOS (TEMPORAL)
# ====================================================================

# Base de datos temporal en memoria para usuarios registrados
# Estructura: {user_id: {id, email, password_hash, nombre, telefono, registered_at}}
# TODO: Migrar a base de datos MySQL real en producción
users_db = {}

# ====================================================================
# SISTEMA DE AUTENTICACIÓN
# ====================================================================

def login_required(f):
    """
    Decorador para proteger rutas que requieren autenticación.
    
    Verifica si el usuario tiene una sesión activa. Si no, redirige 
    al login con un mensaje de error apropiado.
    
    Args:
        f: Función de la ruta a proteger
        
    Returns:
        Función decorada que verifica autenticación
        
    Ejemplo:
        @app.route("/formulario")
        @login_required
        def protected_route():
            return "Solo usuarios autenticados"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('Iniciar_Sesion'))
        return f(*args, **kwargs)
    return decorated_function

def is_authenticated():
    """
    Verifica si el usuario actual está autenticado.
    
    Returns:
        bool: True si hay una sesión activa, False en caso contrario
    """
    return 'user_id' in session

def get_current_user():
    """
    Obtiene los datos del usuario actualmente logueado.
    
    Returns:
        dict: Datos del usuario (id, email, nombre, etc.) o None si no hay sesión
    """
    if 'user_id' in session:
        return users_db.get(session['user_id'])
    return None

@app.context_processor
def inject_auth():
    """
    Context Processor que inyecta información de autenticación en todas las plantillas.
    
    Hace disponibles las variables 'is_authenticated' y 'current_user' en todos 
    los templates Jinja2 sin necesidad de pasarlas explícitamente.
    
    Returns:
        dict: Variables disponibles en templates
    """
    return {
        'is_authenticated': is_authenticated(),
        'current_user': get_current_user()
    }

# ====================================================================
# RUTAS DE PÁGINAS DE MASCOTAS (PÚBLICAS)
# ====================================================================

@app.route("/cachorro")
def Pagina2_Cachorro():
    """
    Página de detalle del Cachorro Schnauzer.
    
    Muestra información detallada, fotos, características y botón de adopción.
    El botón de adopción requiere autenticación (validado en frontend).
    
    Returns:
        Template renderizado con información del cachorro
    """
    return render_template("main/Pagina2_Cachorro.html")

@app.route("/michi")
def Pagina_Michi():
    """
    Página de detalle de Michi (Gato).
    
    Muestra información detallada del gato disponible para adopción.
    Incluye características, cuidados necesarios y proceso de contacto.
    
    Returns:
        Template renderizado con información de Michi
    """
    return render_template("main/Pagina_Michi.html")

@app.route("/rocky")
def Pagina_perro2():
    """
    Página de detalle de Rocky (Perro mestizo).
    
    Información completa sobre Rocky: personalidad, cuidados, requisitos
    para adopción y contacto con la fundación responsable.
    
    Returns:
        Template renderizado con información de Rocky
    """
    return render_template("main/Pagina_perro2.html")

# ====================================================================
# RUTAS PROTEGIDAS (REQUIEREN AUTENTICACIÓN)
# ====================================================================

@app.route("/formulario", methods=["GET", "POST"])
@login_required
def Formulario_Para_Adoptar():
    """
    Formulario de adopción para mascotas.
    
    Ruta protegida que solo permite acceso a usuarios autenticados.
    Procesa solicitudes de adopción y las asocia con el usuario logueado.
    
    Methods:
        GET: Muestra el formulario de adopción
        POST: Procesa la solicitud de adopción
        
    Returns:
        GET: Template del formulario
        POST: Redirección con mensaje de confirmación
        
    Security:
        - Requiere autenticación (@login_required)
        - Asocia solicitud con usuario de la sesión
    """
    if request.method == "POST":
        # Validar datos usando el sistema unificado
        is_valid, errors, validated_data = validate_adoption_data(request.form)
        
        if not is_valid:
            # Mostrar errores de validación
            for field, error in errors.items():
                flash(f'{error}', 'error')
            return render_template("main/Formulario_Para_Adoptar.html")
        
        # Obtener datos del usuario autenticado
        user = get_current_user()
        
        # TODO: Guardar solicitud completa en base de datos
        adoption_request = {
            'user_id': user['id'],
            'nombre': validated_data['nombre'],
            'email': validated_data['email'],
            'telefono': validated_data['telefono'],
            'direccion': validated_data['direccion'],
            'ocupacion': validated_data['ocupacion'],
            'vivienda': validated_data['vivienda'],
            'mascotas': validated_data['mascotas'],
            'motivo': validated_data['motivo'],
            'acepta_terminos': validated_data.get('acepta_terminos', False),
            'fecha_solicitud': __import__('datetime').datetime.now(),
            'estado': 'pendiente'
        }
        
        # TODO: Enviar notificación por email a la fundación
        # TODO: Generar número de seguimiento
        
        flash(f'¡Solicitud de adopción enviada correctamente! Te contactaremos pronto para continuar con el proceso.', 'success')
        return redirect("/adopcion")
    
    return render_template("main/Formulario_Para_Adoptar.html")



# ====================================================================
# RUTAS PÚBLICAS PRINCIPALES
# ====================================================================

@app.route("/")
def Pagina_Principal():
    """
    Página principal/landing del sitio Adopt Me Now.
    
    Presenta la propuesta de valor, estadísticas de adopciones exitosas,
    testimonios de familias adoptantes y call-to-action para ver mascotas.
    
    Features:
        - Hero section con mensaje principal
        - Estadísticas animadas
        - Carrusel de testimonios
        - Efectos visuales (partículas, huellas)
        - Chatbot integrado
        
    Returns:
        Template de la página principal
    """
    return render_template("main/Pagina_Principal.html")


# ====================================================================
# RUTAS DE AUTENTICACIÓN Y GESTIÓN DE USUARIOS
# ====================================================================

@app.route("/registro", methods=["GET", "POST"])
def Registro_Usuario():
    """
    Registro de nuevos usuarios en el sistema.
    
    Permite a las personas interesadas en adoptar crear una cuenta
    para acceder a formularios de adopción y contacto con fundaciones.
    
    Methods:
        GET: Muestra formulario de registro
        POST: Procesa datos de registro y crea usuario
        
    Form Fields:
        - email (required): Email único del usuario
        - password (required): Contraseña (se almacena hasheada)
        - nombre (required): Nombre completo del usuario
        - telefono (optional): Número de contacto
        
    Validations:
        - Campos obligatorios presentes
        - Email único en el sistema
        - Password hasheado con SHA-256
        
    Returns:
        GET: Template de registro
        POST: Redirección a login o formulario con errores
        
    Security:
        - Hash SHA-256 para contraseñas
        - Validación de email único
        - Sanitización de inputs
    """
    if request.method == "POST":
        # Validar datos usando el sistema unificado
        is_valid, errors, validated_data = validate_registration_data(request.form, users_db)
        
        if not is_valid:
            # Mostrar errores de validación
            for field, error in errors.items():
                flash(f'{error}', 'error')
            return render_template("main/Registro_Usuario.html")
        
        # Crear nuevo usuario con datos validados
        user_id = len(users_db) + 1
        hashed_password = hashlib.sha256(validated_data['password'].encode()).hexdigest()
        
        # Almacenar usuario en base de datos temporal
        users_db[user_id] = {
            'id': user_id,
            'email': validated_data['email'],
            'password': hashed_password,
            'nombre': validated_data['nombre'],
            'telefono': validated_data.get('telefono', ''),
            'registered_at': __import__('datetime').datetime.now()
        }
        
        flash('¡Registro exitoso! Ahora puedes iniciar sesión', 'success')
        return redirect("/iniciar-sesion")
    
    # Mostrar formulario de registro
    return render_template("main/Registro_Usuario.html")


@app.route("/iniciar-sesion", methods=["GET", "POST"])
def Iniciar_Sesion():
    """
    Inicio de sesión para usuarios registrados.
    
    Autentica usuarios mediante email/contraseña y establece sesión Flask
    para acceso a funcionalidades protegidas del sistema.
    
    Methods:
        GET: Muestra formulario de login
        POST: Autentica usuario y crea sesión
        
    Form Fields:
        - email: Email registrado del usuario
        - password: Contraseña del usuario
        
    Session Data (on success):
        - user_id: ID único del usuario
        - user_email: Email del usuario
        - user_name: Nombre para personalización
        
    Returns:
        GET: Template de login
        POST: Redirección a home o formulario con errores
        
    Security:
        - Validación de credenciales hasheadas
        - Limpieza de datos de entrada
        - Mensajes de error genéricos (no revelan si email existe)
    """
    if request.method == "POST":
        # Validar datos usando el sistema unificado
        is_valid, errors, validated_data = validate_login_data(request.form)
        
        if not is_valid:
            # Mostrar errores de validación
            for field, error in errors.items():
                flash(f'{error}', 'error')
            return render_template("main/Iniciar_Sesion.html")
        
        email = validated_data['email']
        password = validated_data['password']
        
        # Buscar usuario por email
        user = None
        for u in users_db.values():
            if u['email'] == email:
                user = u
                break
        
        # Validar credenciales (hash de contraseña)
        if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
            # Establecer sesión de usuario
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = user['nombre']
            
            flash(f'¡Bienvenido, {user["nombre"]}!', 'success')
            return redirect("/")
        else:
            # Mensaje genérico por seguridad (no revela si email existe)
            flash('Email o contraseña incorrectos', 'error')
    
    # Mostrar formulario de login
    return render_template("main/Iniciar_Sesion.html")

@app.route("/logout")
def logout():
    """
    Cierre de sesión del usuario actual.
    
    Limpia todos los datos de sesión Flask y redirige al usuario
    a la página principal con mensaje de confirmación.
    
    Returns:
        Redirección a página principal con mensaje informativo
        
    Security:
        - Limpia completamente la sesión Flask
        - No requiere autenticación (disponible siempre)
    """
    session.clear()  # Limpiar todos los datos de sesión
    flash('Has cerrado sesión correctamente', 'info')
    return redirect("/")

# ====================================================================
# RUTAS ADMINISTRATIVAS
# ====================================================================

@app.route("/registro-administrador", methods=["GET", "POST"])
def Registro_Administrador():
    """
    Registro de administradores del sistema.
    
    Permite el registro de personal de fundaciones y administradores
    que pueden gestionar postulaciones de mascotas y adopciones.
    
    TODO: Implementar lógica específica de admin:
        - Validación de códigos de acceso
        - Permisos diferenciados
        - Proceso de aprobación
        
    Methods:
        GET: Muestra formulario de registro admin
        POST: Procesa registro y redirige a login
        
    Returns:
        Template de registro administrativo
    """
    if request.method == "POST":
        # TODO: Implementar validación específica de administradores
        # TODO: Verificar códigos de acceso o invitaciones
        # TODO: Asignar roles y permisos específicos
        return redirect("/iniciar-sesion")
    return render_template("main/Registro_Administrador.html")

# ====================================================================
# RUTAS DE CATÁLOGO Y BÚSQUEDA
# ====================================================================

@app.route("/adopcion")
def Pagina_Adopcion():
    """
    Catálogo principal de mascotas disponibles para adopción.
    
    Lista todas las mascotas disponibles con:
        - Cards individuales con foto y descripción básica
        - Filtros de ordenamiento (nombre, autor, fecha)
        - Sistema de autenticación integrado para botones de contacto
        - Indicadores de estado de usuario (logueado/no logueado)
        
    Features:
        - Grid responsive de cards
        - Ordenamiento dinámico via JavaScript
        - Modal de autenticación para usuarios no logueados
        - Botones de contacto protegidos
        - Información de usuario actual
        
    Returns:
        Template con lista completa de mascotas
    """
    return render_template("main/Pagina1_Adopcion.html")

@app.route("/mascotas")
def Mascotas_Alias():
    """
    Alias de compatibilidad para la ruta /adopcion.
    
    Redirige automáticamente a /adopcion para mantener
    compatibilidad con URLs anteriores o bookmarks.
    
    Returns:
        Redirección 301 a /adopcion
    """
    return redirect("/adopcion")

# ====================================================================
# RUTAS DE FUNDACIONES E INFORMACIÓN
# ====================================================================

@app.route("/fundaciones")
def Pagina_Fundacion():
    """
    Información sobre fundaciones y rescatistas.
    
    Presenta información sobre las organizaciones aliadas,
    sus historias, misión y cómo colaboran con Adopt Me Now.
    
    Content:
        - Lista de fundaciones activas
        - Historias de rescate exitosos  
        - Proceso para unirse como fundación
        - Estadísticas de impacto social
        
    Returns:
        Template con información de fundaciones
    """
    return render_template("main/Pagina_Fundacion.html")

@app.route("/funcuan")
def Pagina_Funcuan():
    """
    Página específica de la Fundación FUNCUAN.
    
    Información detallada sobre FUNCUAN (Fundación Cuidado Animal),
    una de las fundaciones principales aliadas del proyecto.
    
    TODO: Crear template específico con:
        - Historia de la fundación
        - Mascotas bajo su cuidado
        - Formas de contacto directo
        - Galería de adopciones exitosas
        
    Returns:
        Template específico de FUNCUAN (actualmente reutiliza template general)
    """
    # TODO: Crear template específico "main/Pagina_Funcuan.html"
    return render_template("main/Pagina_Fundacion.html")

# ====================================================================
# RUTAS DE GESTIÓN DE MASCOTAS
# ====================================================================

@app.route("/postular", methods=["GET", "POST"])
def Postular_Mascotas():
    """
    Formulario para postular nuevas mascotas al sistema.
    
    Permite a fundaciones y rescatistas registrar nuevas mascotas
    disponibles para adopción en la plataforma.
    
    Methods:
        GET: Muestra formulario de postulación
        POST: Procesa datos y registra nueva mascota
        
    Form Fields (TODO: Implementar):
        - Nombre de la mascota
        - Especie y raza
        - Edad y características
        - Estado de salud y vacunación
        - Fotos
        - Requisitos especiales de adopción
        - Información de contacto de la fundación
        
    TODO: Implementar:
        - Validación de datos completos
        - Upload de imágenes
        - Moderación de contenido
        - Notificaciones automáticas
        
    Returns:
        GET: Template de postulación
        POST: Redirección a catálogo con confirmación
    """
    if request.method == "POST":
        # TODO: Procesar datos del formulario
        # TODO: Validar información de la mascota
        # TODO: Guardar imágenes en sistema de archivos
        # TODO: Enviar notificación de nueva postulación
        # TODO: Generar ID único para seguimiento
        return redirect("/adopcion")
    return render_template("main/Postular_Mascotas.html")


# ====================================================================
# CONFIGURACIÓN DE SERVIDOR Y PUNTO DE ENTRADA
# ====================================================================

if __name__ == "__main__":
    """
    Punto de entrada principal de la aplicación Flask.
    
    Configuración de desarrollo:
        - debug=True: Recarga automática y debugging detallado
        - port=5100: Puerto personalizado para evitar conflictos
        - host="0.0.0.0": Accesible desde otras IPs de la red local
        
    Para acceder:
        - Local: http://localhost:5100
        - Red local: http://[IP-de-tu-maquina]:5100
        
    TODO Para producción:
        - Usar Gunicorn/uWSGI como servidor WSGI
        - Configurar Nginx como proxy reverso
        - Establecer debug=False
        - Usar variables de entorno para configuración
        - Implementar logging apropiado
        - Configurar HTTPS con SSL/TLS
    """
    app.run(debug=True, port=5100, host="0.0.0.0")
