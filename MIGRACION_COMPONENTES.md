# Documentación de Migración a Arquitectura de Componentes

## Resumen
Se ha completado la migración completa de todos los archivos HTML del proyecto Adopt Me a una arquitectura basada en componentes usando el sistema de herencia de templates de Jinja2. **TANTO los archivos de la carpeta `main/` como los de `Vistas/` ahora utilizan la nueva arquitectura**.

## Estructura Implementada

### 1. Template Base
- **Archivo**: `layouts/base.html`
- **Función**: Template principal con bloques extendibles
- **Bloques disponibles**:
  - `title`: Título de la página
  - `stylesheets`: CSS específico por página
  - `background_effects`: Efectos de fondo opcionales
  - `navbar`: Navegación (por defecto incluye navbar estándar)
  - `content`: Contenido principal
  - `footer`: Pie de página (por defecto incluye footer estándar)
  - `scripts`: JavaScript específico por página

### 2. Componentes Reutilizables
Ubicación: `components/`

- **navbar.html**: Navegación principal estándar
- **footer.html**: Pie de página estándar
- **particles.html**: Efectos de partículas animadas
- **paws.html**: Efectos de huellas animadas
- **admin_paws.html**: Efectos de huellas para administrador
- **university_logo.html**: Logo de la universidad

### 3. Archivos Migrados

#### A) Carpeta `Vistas/` (Copia con componentes)
- **home.html** (copia de Pagina_Principal.html)
- **login.html** (copia de Iniciar_Sesion.html)
- **registro_usuario.html** (copia de Registro_Usuario.html)
- **registro_administrador.html** (copia de Registro_Administrador.html)
- **adopcion.html** (copia de Pagina1_Adopcion.html)
- **cachorro.html** (copia de Pagina2_Cachorro.html)
- **fundacion.html** (copia de Pagina_Fundacion.html)
- **formulario_adopcion.html** (copia de Formulario_Para_Adoptar.html)
- **postular_mascotas.html** (copia de Postular_Mascotas.html)

#### B) Carpeta `main/` (Originales convertidos)
- **Pagina_Principal.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`
- **Iniciar_Sesion.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`
- **Registro_Usuario.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`
- **Registro_Administrador.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`
- **Pagina1_Adopcion.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`
- **Pagina2_Cachorro.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`
- **Pagina_Fundacion.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`
- **Formulario_Para_Adoptar.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`
- **Postular_Mascotas.html** ✅ Ahora usa `{% extends "layouts/base.html" %}`

## Rutas Actualizadas en app.py

**Las rutas apuntan nuevamente a los archivos originales de `main/` que ahora usan componentes**:

```python
# Rutas principales (ACTUALIZADAS)
"/" -> "main/Pagina_Principal.html"
"/adopcion" -> "main/Pagina1_Adopcion.html"
"/cachorro" -> "main/Pagina2_Cachorro.html"
"/fundaciones" -> "main/Pagina_Fundacion.html"
"/funcuan" -> "main/Pagina_Fundacion.html"

# Autenticación (ACTUALIZADAS)
"/iniciar-sesion" -> "main/Iniciar_Sesion.html"
"/registro" -> "main/Registro_Usuario.html"
"/registro-administrador" -> "main/Registro_Administrador.html"

# Formularios (ACTUALIZADAS)
"/formulario" -> "main/Formulario_Para_Adoptar.html"
"/postular" -> "main/Postular_Mascotas.html"
```

## Patrones de Conversión Aplicados

### Páginas Estándar (con navbar/footer normal):
```html
{% extends "layouts/base.html" %}
{% block title %}Título{% endblock %}
{% block content %}
  <!-- contenido -->
{% endblock %}
```

### Páginas Sin Navbar/Footer (login, registro):
```html
{% extends "layouts/base.html" %}
{% block navbar %}<!-- No navbar -->{% endblock %}
{% block footer %}<!-- No footer -->{% endblock %}
{% block background_effects %}
  {% include 'components/particles.html' %}
  {% include 'components/paws.html' %}
{% endblock %}
```

### Páginas con Header/Footer Personalizado:
```html
{% extends "layouts/base.html" %}
{% block navbar %}
  <header class="topbar">...</header>
{% endblock %}
{% block footer %}
  <footer class="footer">...</footer>
{% endblock %}
```

## Ventajas Logradas

1. **✅ Reutilización Total**: Componentes definidos una vez, usados por todos
2. **✅ Mantenibilidad**: Cambios en componentes se propagan automáticamente
3. **✅ Consistencia**: Estructura base garantiza diseño uniforme
4. **✅ Flexibilidad**: Override de bloques para casos especiales
5. **✅ Escalabilidad**: Patrón establecido para nuevas páginas
6. **✅ Compatibilidad**: Los archivos originales ahora usan la nueva arquitectura

## Estado Final

✅ **COMPLETADO**: Todos los archivos HTML (main/ y Vistas/) migrados a arquitectura de componentes  
✅ **COMPLETADO**: Rutas actualizadas para usar archivos originales con componentes  
✅ **COMPLETADO**: Funcionalidad preservada al 100%  
✅ **COMPLETADO**: Sistema de herencia de templates implementado  
✅ **COMPLETADO**: Componentes reutilizables creados y funcionando  

**La aplicación ahora utiliza programación por componentes en TODOS los archivos HTML**, manteniendo los nombres originales y la estructura de carpetas existente, pero con la potencia y flexibilidad de la nueva arquitectura.