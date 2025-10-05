#!/usr/bin/env python3
"""
Script para corregir la sintaxis de Jinja2 en los templates.
Convierte la sintaxis 'with' de Django a la sintaxis estándar de Jinja2.
"""

import re
import os

def fix_jinja_syntax(file_path):
    """Corrige la sintaxis with en archivos Jinja2."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patrón para encontrar includes con 'with'
    pattern = r"{% include '([^']+)' with \{([^}]+)\} %}"
    
    def replace_include(match):
        template_path = match.group(1)
        params = match.group(2)
        
        # Formatear los parámetros como variables Jinja2
        formatted_params = params.replace("'", "").strip()
        
        # Crear el nuevo formato
        return f"""{{%- set field_data = {{{params}}} -%}}
                {{%- include '{template_path}' -%}}"""
    
    # Reemplazar todos los matches
    new_content = re.sub(pattern, replace_include, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Corregido: {file_path}")
        return True
    else:
        print(f"⏭️  Sin cambios: {file_path}")
        return False

def main():
    """Función principal para corregir todos los templates."""
    
    templates_dir = "Config/Templates/main"
    
    files_to_fix = [
        "Registro_Usuario.html",
        "Iniciar_Sesion.html", 
        "Formulario_Para_Adoptar.html"
    ]
    
    fixed_count = 0
    
    for filename in files_to_fix:
        file_path = os.path.join(templates_dir, filename)
        if os.path.exists(file_path):
            if fix_jinja_syntax(file_path):
                fixed_count += 1
        else:
            print(f"❌ No encontrado: {file_path}")
    
    print(f"\n🎉 Se corrigieron {fixed_count} archivos")

if __name__ == "__main__":
    main()