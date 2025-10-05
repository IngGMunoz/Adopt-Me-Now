# validation_utils.py
# Sistema de Validación Backend para Adopt Me Now
# 
# Proporciona validación del lado del servidor que complementa
# las validaciones frontend del sistema unificado.

import re
from typing import Dict, List, Any, Optional, Tuple
from functools import wraps
from flask import request, jsonify, flash


class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class FormValidator:
    """
    Validador de formularios para el backend de Adopt Me Now.
    
    Proporciona las mismas reglas de validación que el frontend
    para mantener consistencia y seguridad.
    """
    
    def __init__(self):
        self.errors = {}
        self.validated_data = {}
        
    @staticmethod
    def required(value: Any) -> bool:
        """Verifica que el campo no esté vacío."""
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ''
        return bool(value)
    
    @staticmethod
    def email(value: str) -> bool:
        """Valida formato de email."""
        if not value:
            return False
        pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return re.match(pattern, value) is not None
    
    @staticmethod
    def min_length(value: str, min_len: int) -> bool:
        """Verifica longitud mínima."""
        return len(value) >= min_len if value else False
    
    @staticmethod
    def max_length(value: str, max_len: int) -> bool:
        """Verifica longitud máxima."""
        return len(value) <= max_len if value else True
    
    @staticmethod
    def password(value: str) -> bool:
        """Valida contraseña básica (mínimo 6 caracteres)."""
        return len(value) >= 6 if value else False
    
    @staticmethod
    def password_strong(value: str) -> bool:
        """Valida contraseña fuerte."""
        if not value or len(value) < 8:
            return False
        
        has_upper = bool(re.search(r'[A-Z]', value))
        has_lower = bool(re.search(r'[a-z]', value))
        has_number = bool(re.search(r'\d', value))
        
        return has_upper and has_lower and has_number
    
    @staticmethod
    def phone(value: str) -> bool:
        """Valida número de teléfono."""
        if not value:
            return False
        pattern = r'^[\+]?[0-9\s\-\(\)]{7,15}$'
        return re.match(pattern, value) is not None
    
    @staticmethod
    def name(value: str) -> bool:
        """Valida nombres (solo letras y espacios)."""
        if not value:
            return False
        # Permitir letras, espacios, acentos y ñ
        pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,50}$'
        return re.match(pattern, value.strip()) is not None
    
    @staticmethod
    def alphanumeric(value: str) -> bool:
        """Valida caracteres alfanuméricos."""
        if not value:
            return False
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return re.match(pattern, value) is not None
    
    def validate_field(self, field_name: str, value: Any, rules: str) -> bool:
        """
        Valida un campo específico con las reglas proporcionadas.
        
        Args:
            field_name: Nombre del campo
            value: Valor a validar
            rules: Reglas separadas por |, ej: 'required|email|minLength:5'
            
        Returns:
            True si es válido, False si no
        """
        if not rules:
            return True
            
        rule_list = rules.split('|')
        
        for rule in rule_list:
            if ':' in rule:
                rule_name, param = rule.split(':', 1)
                param = int(param) if param.isdigit() else param
            else:
                rule_name = rule
                param = None
            
            # Obtener método de validación
            validator_method = getattr(self, rule_name.lower(), None)
            if not validator_method:
                continue
            
            # Ejecutar validación
            try:
                if param is not None:
                    is_valid = validator_method(value, param)
                else:
                    is_valid = validator_method(value)
                
                if not is_valid:
                    error_msg = self._get_error_message(rule_name, param)
                    self.errors[field_name] = error_msg
                    return False
                    
            except Exception as e:
                self.errors[field_name] = f"Error de validación: {str(e)}"
                return False
        
        # Si pasó todas las validaciones, guardar el valor limpio
        self.validated_data[field_name] = self._clean_value(value)
        return True
    
    def _get_error_message(self, rule_name: str, param: Any = None) -> str:
        """Obtiene el mensaje de error apropiado para una regla."""
        messages = {
            'required': 'Este campo es obligatorio',
            'email': 'Ingresa un email válido',
            'min_length': f'Mínimo {param} caracteres' if param else 'Muy corto',
            'max_length': f'Máximo {param} caracteres' if param else 'Muy largo',
            'password': 'La contraseña debe tener al menos 6 caracteres',
            'password_strong': 'Contraseña débil. Incluye mayúsculas, minúsculas y números',
            'phone': 'Ingresa un teléfono válido',
            'name': 'Solo letras y espacios, entre 2 y 50 caracteres',
            'alphanumeric': 'Solo letras, números y guiones bajos (3-20 caracteres)'
        }
        return messages.get(rule_name, 'Campo inválido')
    
    def _clean_value(self, value: Any) -> Any:
        """Limpia y normaliza un valor."""
        if isinstance(value, str):
            return value.strip()
        return value
    
    def validate_form(self, form_rules: Dict[str, str], data: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida un formulario completo.
        
        Args:
            form_rules: Diccionario con campo -> reglas
            data: Datos del formulario (opcional, usa request.form si no se proporciona)
            
        Returns:
            Tupla (es_válido, datos_validados)
        """
        if data is None:
            data = request.form.to_dict()
        
        self.errors = {}
        self.validated_data = {}
        
        for field_name, rules in form_rules.items():
            field_value = data.get(field_name, '')
            self.validate_field(field_name, field_value, rules)
        
        return len(self.errors) == 0, self.validated_data
    
    def get_errors(self) -> Dict[str, str]:
        """Obtiene los errores de validación."""
        return self.errors
    
    def add_error(self, field: str, message: str):
        """Agrega un error manualmente."""
        self.errors[field] = message


# Decorador para validación automática de formularios
def validate_form(form_rules: Dict[str, str], redirect_on_error: str = None):
    """
    Decorador para validar formularios automáticamente.
    
    Usage:
        @validate_form({
            'email': 'required|email',
            'password': 'required|password'
        })
        def login():
            # Los datos validados están en request.validated_data
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            validator = FormValidator()
            is_valid, validated_data = validator.validate_form(form_rules)
            
            # Agregar datos validados al request
            request.validated_data = validated_data
            request.validation_errors = validator.get_errors()
            
            if not is_valid:
                # Flash errors para mostrar en el frontend
                for field, error in validator.get_errors().items():
                    flash(f'{field.title()}: {error}', 'error')
                
                if redirect_on_error:
                    from flask import redirect, url_for
                    return redirect(url_for(redirect_on_error))
                else:
                    # Retornar JSON si es una petición AJAX
                    if request.is_json or request.headers.get('Content-Type') == 'application/json':
                        return jsonify({
                            'success': False,
                            'errors': validator.get_errors()
                        }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Reglas predefinidas para los formularios de Adopt Me Now
FORM_RULES = {
    'registration': {
        'nombre': 'required|name',
        'email': 'required|email',
        'telefono': 'phone',
        'password': 'required|password'
    },
    
    'login': {
        'email': 'required|email',
        'password': 'required'
    },
    
    'adoption': {
        'nombre': 'required|name',
        'email': 'required|email',
        'telefono': 'required|phone',
        'direccion': 'required|min_length:5',
        'ocupacion': 'required|min_length:2',
        'vivienda': 'required',
        'mascotas': 'required',
        'motivo': 'required|min_length:10|max_length:500'
    },
    
    'admin_registration': {
        'usuario': 'required|alphanumeric',
        'email': 'required|email',
        'password': 'required|password_strong',
        'nombre': 'required|name',
        'cargo': 'required|min_length:2'
    }
}


class UserValidator:
    """Validaciones específicas para usuarios."""
    
    @staticmethod
    def email_unique(email: str, users_db: dict) -> bool:
        """Verifica que el email sea único."""
        return not any(user['email'] == email for user in users_db.values())
    
    @staticmethod
    def username_unique(username: str, users_db: dict) -> bool:
        """Verifica que el nombre de usuario sea único."""
        return not any(user.get('username') == username for user in users_db.values())


# Funciones de utilidad para validación en las rutas
def validate_registration_data(form_data: dict, users_db: dict) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """
    Valida datos de registro de usuario.
    
    Returns:
        Tupla (es_válido, errores, datos_limpios)
    """
    validator = FormValidator()
    is_valid, validated_data = validator.validate_form(FORM_RULES['registration'], form_data)
    
    if is_valid:
        # Validaciones adicionales específicas del negocio
        email = validated_data.get('email')
        if email and not UserValidator.email_unique(email, users_db):
            validator.add_error('email', 'Este email ya está registrado')
            is_valid = False
    
    return is_valid, validator.get_errors(), validated_data


def validate_login_data(form_data: dict) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """
    Valida datos de login.
    
    Returns:
        Tupla (es_válido, errores, datos_limpios)
    """
    validator = FormValidator()
    is_valid, validated_data = validator.validate_form(FORM_RULES['login'], form_data)
    return is_valid, validator.get_errors(), validated_data


def validate_adoption_data(form_data: dict) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """
    Valida datos del formulario de adopción.
    
    Returns:
        Tupla (es_válido, errores, datos_limpios)
    """
    validator = FormValidator()
    is_valid, validated_data = validator.validate_form(FORM_RULES['adoption'], form_data)
    
    # Validaciones adicionales si es necesario
    if is_valid:
        # Ejemplo: verificar que el tipo de vivienda sea apropiado
        vivienda = validated_data.get('vivienda')
        if vivienda not in ['casa', 'apartamento', 'finca', 'otro']:
            validator.add_error('vivienda', 'Tipo de vivienda no válido')
            is_valid = False
    
    return is_valid, validator.get_errors(), validated_data


# Middleware para validación automática basada en rutas
def setup_validation_middleware(app):
    """Configura middleware de validación para la aplicación Flask."""
    
    @app.before_request
    def validate_request():
        """Valida requests automáticamente basado en la ruta."""
        
        # Mapeo de rutas a reglas de validación
        route_rules = {
            '/registro': FORM_RULES['registration'],
            '/iniciar-sesion': FORM_RULES['login'],
            '/formulario': FORM_RULES['adoption']
        }
        
        # Solo validar POST requests
        if request.method == 'POST' and request.endpoint:
            rules = route_rules.get(request.path)
            if rules:
                validator = FormValidator()
                is_valid, validated_data = validator.validate_form(rules)
                
                # Agregar resultados al request
                request.is_form_valid = is_valid
                request.validated_data = validated_data
                request.validation_errors = validator.get_errors()


# Función para generar respuesta de error estándar
def validation_error_response(errors: Dict[str, str], status_code: int = 400) -> dict:
    """
    Genera respuesta estándar para errores de validación.
    
    Args:
        errors: Diccionario de errores
        status_code: Código de estado HTTP
        
    Returns:
        Diccionario con formato de respuesta estándar
    """
    return {
        'success': False,
        'message': 'Errores de validación encontrados',
        'errors': errors,
        'status_code': status_code
    }


# Ejemplo de uso en las rutas:
"""
from validation_utils import validate_registration_data, validation_error_response

@app.route('/registro', methods=['POST'])
def registro_usuario():
    is_valid, errors, data = validate_registration_data(request.form, users_db)
    
    if not is_valid:
        for field, error in errors.items():
            flash(f'{error}', 'error')
        return render_template('main/Registro_Usuario.html')
    
    # Procesar registro con datos validados
    user_id = len(users_db) + 1
    users_db[user_id] = {
        'id': user_id,
        'nombre': data['nombre'],
        'email': data['email'],
        'telefono': data.get('telefono', ''),
        'password': hashlib.sha256(data['password'].encode()).hexdigest(),
        'registered_at': datetime.now()
    }
    
    flash('Registro exitoso', 'success')
    return redirect('/iniciar-sesion')
"""