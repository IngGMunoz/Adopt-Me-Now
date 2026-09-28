"""Modo demo (DEMO_MODE=true): cuentas de prueba públicas con datos de ejemplo.

Las credenciales están en el README para que cualquiera pruebe la app sin registrarse.
Por eso nadie puede editar, desactivar ni eliminar estas dos cuentas.
"""

from flask import current_app, request, session

from Config.db import db

FUNDACION = {"username": "fundacion", "email": "fundacion@demo.com", "password": "DemoFundacion1"}
ADOPTANTE = {"username": "adoptante", "email": "adoptante@demo.com", "password": "DemoAdoptante1"}

_ENDPOINTS_ADMIN = {"routes_adminC.admin_update_admin", "routes_adminC.admin_delete_admin"}
_ENDPOINTS_USUARIO = {"routes_adminC.admin_update_user", "routes_adminC.admin_delete_user",
                      "routes_UserC.update_user", "routes_UserC.delete_user"}


def sembrar_demo():
    """Crea las cuentas de prueba, una solicitud y una postulación. Solo la primera vez."""
    from Models.admins import admin
    from Models.adoptar_mascotas import adoptar_mascotas
    from Models.mascotas import Mascota
    from Models.postular_mascotas import PostularMascotas
    from Models.usuario import usuario

    if admin.query.filter_by(email=FUNDACION["email"]).first():
        return
    fundacion = admin(username=FUNDACION["username"], email=FUNDACION["email"])
    fundacion.set_password(FUNDACION["password"])
    adoptante = usuario(username=ADOPTANTE["username"], email=ADOPTANTE["email"])
    adoptante.set_password(ADOPTANTE["password"])
    db.session.add_all([fundacion, adoptante])
    db.session.flush()

    michi = Mascota.query.filter_by(nombre="Michi").first()
    db.session.add(adoptar_mascotas(
        username="Adoptante de prueba", email=ADOPTANTE["email"], telefono="300 000 0000",
        vivienda="apartamento", tiene_mascotas="no",
        motivo="Trabajo desde casa y tengo tiempo para acompañarla y llevarla al veterinario.",
        mascota=michi, pet_name=michi.nombre if michi else "Michi", adopter_id=adoptante.id,
    ))
    db.session.add(PostularMascotas(
        nombre="Canela", especie="perro", raza="Criolla", edad="3 años", sexo="hembra",
        tamanio="mediano", ubicacion="Soledad, Atlántico", usuario_id=adoptante.id,
    ))
    db.session.commit()


def proteger_cuentas_demo():
    """before_request: bloquea los cambios sobre las cuentas de prueba."""
    from Config.auth import rechazar
    from Models.admins import admin
    from Models.usuario import usuario

    if not current_app.config["DEMO_MODE"] or request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    endpoint, args = request.endpoint or "", request.view_args or {}
    if endpoint in _ENDPOINTS_ADMIN:
        cuenta = db.session.get(admin, args["aid"])
    elif endpoint in _ENDPOINTS_USUARIO:
        cuenta = db.session.get(usuario, args.get("uid") or args.get("user_id"))
    elif endpoint.startswith("routes_CuentaC.") and not session.get("is_admin"):
        cuenta = db.session.get(usuario, session.get("user_id"))
    else:
        return None
    if cuenta and cuenta.email in (FUNDACION["email"], ADOPTANTE["email"]):
        return rechazar(403, "Las cuentas de prueba no se pueden modificar en la demo pública.")
    return None
