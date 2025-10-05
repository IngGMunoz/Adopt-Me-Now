/**
 * Sistema de Validación Unificado - Adopt Me Now
 * 
 * Componente central para validación de formularios en toda la aplicación.
 * Proporciona validación en tiempo real, mensajes de error consistentes y
 * feedback visual unificado para todos los formularios.
 * 
 * @author Adopt Me Now Team
 * @version 1.0.0
 */

class AdoptMeValidator {
    constructor() {
        this.rules = {
            // Reglas básicas de validación
            required: {
                test: (value) => value && value.trim() !== '',
                message: 'Este campo es obligatorio'
            },
            email: {
                test: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
                message: 'Ingresa un email válido'
            },
            minLength: {
                test: (value, min) => value && value.length >= min,
                message: (min) => `Mínimo ${min} caracteres`
            },
            maxLength: {
                test: (value, max) => !value || value.length <= max,
                message: (max) => `Máximo ${max} caracteres`
            },
            password: {
                test: (value) => value && value.length >= 6,
                message: 'La contraseña debe tener al menos 6 caracteres'
            },
            passwordStrong: {
                test: (value) => {
                    if (!value) return false;
                    const hasUpper = /[A-Z]/.test(value);
                    const hasLower = /[a-z]/.test(value);
                    const hasNumber = /\d/.test(value);
                    const hasSymbol = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?]/.test(value);
                    return value.length >= 8 && hasUpper && hasLower && hasNumber;
                },
                message: 'Contraseña débil. Incluye mayúsculas, minúsculas y números'
            },
            phone: {
                test: (value) => /^[\+]?[0-9\s\-\(\)]{7,15}$/.test(value),
                message: 'Ingresa un teléfono válido'
            },
            name: {
                test: (value) => value && /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,50}$/.test(value.trim()),
                message: 'Solo letras y espacios, entre 2 y 50 caracteres'
            },
            alphanumeric: {
                test: (value) => /^[a-zA-Z0-9_]{3,20}$/.test(value),
                message: 'Solo letras, números y guiones bajos (3-20 caracteres)'
            }
        };

        this.forms = new Map();
        this.initialized = false;
    }

    /**
     * Inicializa el sistema de validación
     */
    init() {
        if (this.initialized) return;
        
        document.addEventListener('DOMContentLoaded', () => {
            this.attachGlobalListeners();
            this.scanForForms();
        });

        this.initialized = true;
    }

    /**
     * Escanea el documento en busca de formularios con validación
     */
    scanForForms() {
        const forms = document.querySelectorAll('[data-validate]');
        forms.forEach(form => this.registerForm(form));
    }

    /**
     * Registra un formulario para validación
     * @param {HTMLFormElement} form - El formulario a registrar
     * @param {Object} customRules - Reglas personalizadas opcionales
     */
    registerForm(form, customRules = {}) {
        if (!form || form.tagName !== 'FORM') {
            console.error('AdoptMeValidator: Elemento no es un formulario válido');
            return;
        }

        const formId = form.id || `form_${Date.now()}`;
        if (!form.id) form.id = formId;

        const formConfig = {
            element: form,
            fields: new Map(),
            customRules: { ...customRules },
            isValid: false,
            submitCallback: null
        };

        // Escanear campos del formulario
        this.scanFormFields(formConfig);

        // Agregar event listeners
        this.attachFormListeners(formConfig);

        this.forms.set(formId, formConfig);
        
        console.log(`AdoptMeValidator: Formulario '${formId}' registrado con ${formConfig.fields.size} campos`);
        return formId;
    }

    /**
     * Escanea y registra los campos de un formulario
     * @param {Object} formConfig - Configuración del formulario
     */
    scanFormFields(formConfig) {
        const fields = formConfig.element.querySelectorAll('[data-validate]');
        
        fields.forEach(field => {
            const fieldName = field.name || field.id;
            if (!fieldName) {
                console.warn('AdoptMeValidator: Campo sin nombre ni ID encontrado');
                return;
            }

            const rules = this.parseFieldRules(field);
            const fieldConfig = {
                element: field,
                rules: rules,
                isValid: false,
                errorElement: null,
                hasBeenTouched: false
            };

            // Crear elemento de error si no existe
            this.createErrorElement(fieldConfig);

            formConfig.fields.set(fieldName, fieldConfig);
        });
    }

    /**
     * Parsea las reglas de validación de un campo
     * @param {HTMLElement} field - El campo del formulario
     * @returns {Array} Array de reglas de validación
     */
    parseFieldRules(field) {
        const rules = [];
        const validateAttr = field.getAttribute('data-validate');
        
        if (validateAttr) {
            const ruleNames = validateAttr.split('|');
            
            ruleNames.forEach(ruleName => {
                const [name, param] = ruleName.split(':');
                const rule = this.rules[name];
                
                if (rule) {
                    rules.push({
                        name: name,
                        rule: rule,
                        param: param ? (isNaN(param) ? param : Number(param)) : undefined
                    });
                } else {
                    console.warn(`AdoptMeValidator: Regla '${name}' no encontrada`);
                }
            });
        }

        // Agregar regla 'required' si el campo tiene el atributo required
        if (field.hasAttribute('required') && !rules.some(r => r.name === 'required')) {
            rules.unshift({
                name: 'required',
                rule: this.rules.required
            });
        }

        return rules;
    }

    /**
     * Crea el elemento para mostrar errores de validación
     * @param {Object} fieldConfig - Configuración del campo
     */
    createErrorElement(fieldConfig) {
        const field = fieldConfig.element;
        const fieldName = field.name || field.id;
        
        // Buscar elemento de error existente
        let errorElement = document.getElementById(`${fieldName}_error`);
        
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = `${fieldName}_error`;
            errorElement.className = 'validation-error';
            errorElement.setAttribute('role', 'alert');
            errorElement.setAttribute('aria-live', 'polite');
            
            // Insertar después del campo o su contenedor
            const container = field.closest('.form-group') || field.closest('.input-container') || field.parentNode;
            if (container.nextSibling) {
                container.parentNode.insertBefore(errorElement, container.nextSibling);
            } else {
                container.parentNode.appendChild(errorElement);
            }
        }
        
        fieldConfig.errorElement = errorElement;
    }

    /**
     * Adjunta event listeners a un formulario
     * @param {Object} formConfig - Configuración del formulario
     */
    attachFormListeners(formConfig) {
        const form = formConfig.element;

        // Validación en tiempo real
        formConfig.fields.forEach((fieldConfig, fieldName) => {
            const field = fieldConfig.element;

            // Validar al salir del campo (blur)
            field.addEventListener('blur', () => {
                fieldConfig.hasBeenTouched = true;
                this.validateField(fieldConfig);
                this.updateFormValidation(formConfig);
            });

            // Validar mientras se escribe (con debounce)
            let timeout;
            field.addEventListener('input', () => {
                clearTimeout(timeout);
                
                if (fieldConfig.hasBeenTouched) {
                    timeout = setTimeout(() => {
                        this.validateField(fieldConfig);
                        this.updateFormValidation(formConfig);
                    }, 300);
                }

                // Feedback visual inmediato para algunos tipos
                this.provideLiveFeedback(fieldConfig);
            });
        });

        // Validar todo el formulario al enviar
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Marcar todos los campos como tocados
            formConfig.fields.forEach(fieldConfig => {
                fieldConfig.hasBeenTouched = true;
            });

            const isValid = this.validateForm(formConfig);
            
            if (isValid) {
                // Ejecutar callback personalizado si existe
                if (formConfig.submitCallback) {
                    formConfig.submitCallback(form);
                } else {
                    // Envío normal del formulario
                    form.submit();
                }
            } else {
                // Scroll al primer error
                this.scrollToFirstError(formConfig);
            }
        });
    }

    /**
     * Adjunta listeners globales
     */
    attachGlobalListeners() {
        // Validar formularios dinámicamente agregados
        document.addEventListener('DOMNodeInserted', (e) => {
            if (e.target.nodeType === 1) {
                const forms = e.target.querySelectorAll ? 
                    e.target.querySelectorAll('[data-validate]') : 
                    (e.target.hasAttribute && e.target.hasAttribute('data-validate') ? [e.target] : []);
                
                forms.forEach(form => {
                    if (form.tagName === 'FORM') {
                        this.registerForm(form);
                    }
                });
            }
        });
    }

    /**
     * Valida un campo específico
     * @param {Object} fieldConfig - Configuración del campo
     * @returns {boolean} - True si el campo es válido
     */
    validateField(fieldConfig) {
        const field = fieldConfig.element;
        const value = field.value;
        let isValid = true;
        let errorMessage = '';

        // Ejecutar todas las reglas de validación
        for (const ruleConfig of fieldConfig.rules) {
            const { rule, param } = ruleConfig;
            
            if (!rule.test(value, param)) {
                isValid = false;
                errorMessage = typeof rule.message === 'function' ? 
                    rule.message(param) : rule.message;
                break; // Mostrar solo el primer error
            }
        }

        fieldConfig.isValid = isValid;
        this.updateFieldUI(fieldConfig, isValid, errorMessage);
        
        return isValid;
    }

    /**
     * Valida todo un formulario
     * @param {Object} formConfig - Configuración del formulario
     * @returns {boolean} - True si el formulario es válido
     */
    validateForm(formConfig) {
        let isFormValid = true;

        formConfig.fields.forEach(fieldConfig => {
            const fieldValid = this.validateField(fieldConfig);
            if (!fieldValid) {
                isFormValid = false;
            }
        });

        formConfig.isValid = isFormValid;
        this.updateFormUI(formConfig);
        
        return isFormValid;
    }

    /**
     * Actualiza la validación del formulario
     * @param {Object} formConfig - Configuración del formulario
     */
    updateFormValidation(formConfig) {
        let isFormValid = true;
        
        formConfig.fields.forEach(fieldConfig => {
            if (!fieldConfig.isValid) {
                isFormValid = false;
            }
        });

        formConfig.isValid = isFormValid;
        this.updateFormUI(formConfig);
    }

    /**
     * Actualiza la UI de un campo específico
     * @param {Object} fieldConfig - Configuración del campo
     * @param {boolean} isValid - Si el campo es válido
     * @param {string} errorMessage - Mensaje de error
     */
    updateFieldUI(fieldConfig, isValid, errorMessage = '') {
        const field = fieldConfig.element;
        const errorElement = fieldConfig.errorElement;

        // Remover clases anteriores
        field.classList.remove('valid', 'invalid');
        
        // Agregar clase apropiada
        field.classList.add(isValid ? 'valid' : 'invalid');

        // Actualizar mensaje de error
        if (errorElement) {
            if (isValid) {
                errorElement.textContent = '';
                errorElement.style.display = 'none';
                errorElement.removeAttribute('aria-describedby');
            } else {
                errorElement.textContent = errorMessage;
                errorElement.style.display = 'block';
                field.setAttribute('aria-describedby', errorElement.id);
            }
        }

        // Efectos visuales adicionales
        this.addFieldAnimation(field, isValid);
    }

    /**
     * Actualiza la UI del formulario completo
     * @param {Object} formConfig - Configuración del formulario
     */
    updateFormUI(formConfig) {
        const form = formConfig.element;
        const submitButton = form.querySelector('[type="submit"]');
        
        // Habilitar/deshabilitar botón de envío
        if (submitButton) {
            if (formConfig.isValid) {
                submitButton.removeAttribute('disabled');
                submitButton.classList.remove('disabled');
                submitButton.classList.add('enabled');
            } else {
                submitButton.setAttribute('disabled', 'disabled');
                submitButton.classList.remove('enabled');
                submitButton.classList.add('disabled');
            }
        }

        // Agregar clase al formulario
        form.classList.toggle('form-valid', formConfig.isValid);
        form.classList.toggle('form-invalid', !formConfig.isValid);
    }

    /**
     * Proporciona feedback visual en tiempo real
     * @param {Object} fieldConfig - Configuración del campo
     */
    provideLiveFeedback(fieldConfig) {
        const field = fieldConfig.element;
        const value = field.value;

        // Feedback específico para contraseñas
        if (field.type === 'password') {
            this.updatePasswordStrength(field, value);
        }

        // Feedback para emails
        if (field.type === 'email' && value) {
            const isValidFormat = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            field.classList.toggle('email-preview', isValidFormat);
        }
    }

    /**
     * Actualiza el indicador de fortaleza de contraseña
     * @param {HTMLElement} field - Campo de contraseña
     * @param {string} value - Valor de la contraseña
     */
    updatePasswordStrength(field, value) {
        const strengthElement = field.parentNode.querySelector('.password-strength') ||
                              field.closest('.form-group')?.querySelector('.password-strength');
        
        if (!strengthElement) return;

        const strength = this.calculatePasswordStrength(value);
        const strengthFill = strengthElement.querySelector('.password-strength-fill');
        
        if (strengthFill) {
            strengthFill.style.width = `${strength.percentage}%`;
            strengthFill.className = `password-strength-fill strength-${strength.level}`;
            
            // Agregar tooltip con sugerencias
            strengthElement.title = strength.suggestions.join(', ');
        }
    }

    /**
     * Calcula la fortaleza de una contraseña
     * @param {string} password - La contraseña a evaluar
     * @returns {Object} - Información sobre la fortaleza
     */
    calculatePasswordStrength(password) {
        if (!password) return { level: 'none', percentage: 0, suggestions: [] };

        let score = 0;
        const suggestions = [];

        // Criterios de evaluación
        if (password.length >= 8) score += 25;
        else suggestions.push('Al menos 8 caracteres');

        if (/[A-Z]/.test(password)) score += 25;
        else suggestions.push('Incluir mayúsculas');

        if (/[a-z]/.test(password)) score += 25;
        else suggestions.push('Incluir minúsculas');

        if (/\d/.test(password)) score += 15;
        else suggestions.push('Incluir números');

        if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?]/.test(password)) {
            score += 10;
        } else {
            suggestions.push('Incluir símbolos');
        }

        // Determinar nivel
        let level;
        if (score < 25) level = 'weak';
        else if (score < 50) level = 'fair';
        else if (score < 75) level = 'good';
        else level = 'strong';

        return { level, percentage: score, suggestions };
    }

    /**
     * Agrega animación a un campo
     * @param {HTMLElement} field - El campo
     * @param {boolean} isValid - Si es válido
     */
    addFieldAnimation(field, isValid) {
        // Remover animaciones anteriores
        field.classList.remove('field-error-shake', 'field-success-glow');

        if (isValid) {
            field.classList.add('field-success-glow');
            setTimeout(() => field.classList.remove('field-success-glow'), 1000);
        } else {
            field.classList.add('field-error-shake');
            setTimeout(() => field.classList.remove('field-error-shake'), 500);
        }
    }

    /**
     * Hace scroll al primer error en el formulario
     * @param {Object} formConfig - Configuración del formulario
     */
    scrollToFirstError(formConfig) {
        const firstInvalidField = Array.from(formConfig.fields.values())
            .find(fieldConfig => !fieldConfig.isValid);

        if (firstInvalidField) {
            firstInvalidField.element.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
            firstInvalidField.element.focus();
        }
    }

    /**
     * Establece un callback personalizado para el envío del formulario
     * @param {string} formId - ID del formulario
     * @param {Function} callback - Función callback
     */
    setSubmitCallback(formId, callback) {
        const formConfig = this.forms.get(formId);
        if (formConfig) {
            formConfig.submitCallback = callback;
        }
    }

    /**
     * Agrega una regla de validación personalizada
     * @param {string} name - Nombre de la regla
     * @param {Function} test - Función de validación
     * @param {string|Function} message - Mensaje de error
     */
    addCustomRule(name, test, message) {
        this.rules[name] = { test, message };
    }

    /**
     * Valida un formulario manualmente por ID
     * @param {string} formId - ID del formulario
     * @returns {boolean} - True si es válido
     */
    validateFormById(formId) {
        const formConfig = this.forms.get(formId);
        return formConfig ? this.validateForm(formConfig) : false;
    }

    /**
     * Limpia todos los errores de un formulario
     * @param {string} formId - ID del formulario
     */
    clearFormErrors(formId) {
        const formConfig = this.forms.get(formId);
        if (formConfig) {
            formConfig.fields.forEach(fieldConfig => {
                fieldConfig.element.classList.remove('valid', 'invalid');
                if (fieldConfig.errorElement) {
                    fieldConfig.errorElement.textContent = '';
                    fieldConfig.errorElement.style.display = 'none';
                }
            });
        }
    }
}

// Crear instancia global
window.AdoptMeValidator = new AdoptMeValidator();

// Inicializar automáticamente cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.AdoptMeValidator.init();
    });
} else {
    window.AdoptMeValidator.init();
}

// Export para uso modular
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdoptMeValidator;
}