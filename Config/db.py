"""
CONFIGURACIÓN DE BASE DE DATOS Y APLICACIÓN FLASK
==================================================

Este módulo configura la instancia principal de Flask con todas las 
configuraciones necesarias para el proyecto Adopt Me Now:

- Rutas de templates y archivos estáticos
- Conexión a base de datos MySQL
- Extensiones de Flask (SQLAlchemy, Marshmallow)
- Configuración de paths absolutos

Autor: Equipo Adopt Me Now
"""

from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# ====================================================================
# CONFIGURACIÓN DE RUTAS DE ARCHIVOS
# ====================================================================

# Directorio actual (Config/)
BASE_DIR = os.path.dirname(__file__)

# Directorio raíz del proyecto (nivel superior)
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Directorio de templates HTML (Config/Templates/)
# Contiene: layouts/, components/, main/, Vistas/
TEMPLATE_DIR = os.path.join(BASE_DIR, 'Templates')

# Directorio de archivos estáticos (static/)
# Contiene: css/, images/, JS/
STATIC_DIR = os.path.join(PROJECT_ROOT, 'static')

# ====================================================================
# CONFIGURACIÓN DE APLICACIÓN FLASK
# ====================================================================

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,    # Templates Jinja2 desde Config/Templates/
    static_folder=STATIC_DIR,        # CSS/JS/Images desde /static/
    static_url_path='/static'        # URL base para archivos estáticos
)

# ====================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ====================================================================

# Conexión MySQL con PyMySQL
# TODO: Usar variables de entorno para credenciales en producción
# TODO: Crear base de datos específica del proyecto (adopt_me_db)
# String de conexión a MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/mysql'

# Desactivar tracking de modificaciones (mejora performance)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Clave secreta básica (será sobrescrita en app.py)
# TODO: Remover esta clave y usar solo la configurada en app.py
app.secret_key = "web"

# ====================================================================
# INSTANCIAS DE EXTENSIONES FLASK
# ====================================================================

# SQLAlchemy - ORM para interacción con base de datos
# Permite definir modelos de datos y realizar queries de forma pythónica
db = SQLAlchemy(app)

# Marshmallow - Serialización/deserialización de datos
# Útil para APIs REST y validación de esquemas de datos
ma = Marshmallow(app)

# ====================================================================
# NOTAS DE IMPLEMENTACIÓN
# ====================================================================

"""
ESTADO ACTUAL:
- Configuración básica lista para usar
- Base de datos MySQL configurada pero no utilizada
- Modelos de datos no implementados (se usa diccionario temporal)

TODO PARA PRODUCCIÓN:
1. Crear modelos SQLAlchemy:
   - User (usuarios registrados)
   - Pet (mascotas en adopción)  
   - AdoptionRequest (solicitudes de adopción)
   - Foundation (fundaciones aliadas)

2. Implementar migraciones con Flask-Migrate

3. Configurar variables de entorno:
   - DATABASE_URL
   - SECRET_KEY
   - FLASK_ENV

4. Agregar configuración por entornos (desarrollo/producción)
"""