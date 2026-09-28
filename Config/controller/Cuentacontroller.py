"""Área personal del usuario: actividad, solicitudes, postulaciones y configuración."""

from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from Config.actividad import agrupar_por_dia, registrar
from Config.auth import check_login, is_admin
from Config.db import db
from Models.actividad import Actividad
from Models.admins import admin as AdminModel
from Models.usuario import usuario

routes_CuentaC = Blueprint("routes_CuentaC", __name__, url_prefix="/mi-cuenta")

MIN_PASSWORD = 8


def usuario_requerido(f):
    """Solo para usuarios normales: los administradores tienen su propio panel."""
    @wraps(f)
    def decorated(*args, **kwargs):
        denied = check_login()
        if denied:
            return denied
        if is_admin():
            return redirect(url_for("Postular_Admin"))
        u = db.session.get(usuario, session["user_id"])
        if not u:
            session.clear()
            return redirect(url_for("Iniciar_Sesion"))
        return f(u, *args, **kwargs)
    return decorated


def _volver(seccion):
    return redirect(url_for("routes_CuentaC.mi_cuenta") + "#" + seccion)


@routes_CuentaC.route("/")
@usuario_requerido
def mi_cuenta(u):
    tipo = request.args.get("tipo")
    actividades = Actividad.query.filter_by(usuario_id=u.id)
    if tipo in Actividad.TIPOS:
        actividades = actividades.filter_by(tipo=tipo)
    actividades = actividades.order_by(Actividad.created_at.desc(), Actividad.id.desc()).limit(100).all()

    solicitudes = sorted(u.solicitudes, key=lambda s: s.id, reverse=True)
    postulaciones = sorted(u.postulaciones, key=lambda p: p.id, reverse=True)
    return render_template(
        "main/Mi_Cuenta.html",
        u=u,
        grupos=agrupar_por_dia(actividades),
        total_actividades=len(actividades),
        tipo_actual=tipo if tipo in Actividad.TIPOS else None,
        tipos=Actividad.TIPOS,
        solicitudes=solicitudes,
        postulaciones=postulaciones,
    )


@routes_CuentaC.route("/perfil", methods=["POST"])
@usuario_requerido
def actualizar_perfil(u):
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip()

    if len(username) < 3 or "@" not in email:
        flash("Escribe un nombre de usuario (mínimo 3 caracteres) y un correo válido", "error")
        return _volver("configuracion")

    ocupado = usuario.query.filter(
        usuario.id != u.id, (usuario.username == username) | (usuario.email == email)
    ).first() or AdminModel.query.filter((AdminModel.username == username) | (AdminModel.email == email)).first()
    if ocupado:
        flash("Ese nombre de usuario o correo ya está en uso", "error")
        return _volver("configuracion")

    cambios = []
    if username != u.username:
        cambios.append("nombre de usuario")
    if email != u.email:
        cambios.append("correo")
    if not cambios:
        flash("No hubo cambios en tu perfil", "info")
        return _volver("configuracion")

    u.username = username
    u.email = email
    registrar(u.id, "perfil_actualizado", f"Actualizaste tu {' y '.join(cambios)}", commit=False)
    db.session.commit()
    session["user_name"] = u.username
    session["user_email"] = u.email
    flash("Tu perfil se actualizó correctamente", "success")
    return _volver("configuracion")


@routes_CuentaC.route("/contrasena", methods=["POST"])
@usuario_requerido
def cambiar_contrasena(u):
    actual = request.form.get("actual") or ""
    nueva = request.form.get("nueva") or ""
    confirmacion = request.form.get("confirmacion") or ""

    if not u.check_password(actual):
        flash("Tu contraseña actual no es correcta", "error")
    elif len(nueva) < MIN_PASSWORD:
        flash(f"La nueva contraseña debe tener al menos {MIN_PASSWORD} caracteres", "error")
    elif nueva != confirmacion:
        flash("Las contraseñas nuevas no coinciden", "error")
    elif u.check_password(nueva):
        flash("La nueva contraseña debe ser distinta de la actual", "error")
    else:
        u.set_password(nueva)
        registrar(u.id, "contrasena_cambiada", "Cambiaste tu contraseña", commit=False)
        db.session.commit()
        flash("Tu contraseña se cambió correctamente", "success")
    return _volver("configuracion")


@routes_CuentaC.route("/eliminar", methods=["POST"])
@usuario_requerido
def eliminar_cuenta(u):
    if not u.check_password(request.form.get("password") or ""):
        flash("La contraseña no es correcta. Tu cuenta no se eliminó.", "error")
        return _volver("configuracion")
    # Las solicitudes y postulaciones se conservan (sin usuario) para el historial de la fundación;
    # la actividad personal se elimina con la cuenta.
    db.session.delete(u)
    db.session.commit()
    session.clear()
    flash("Tu cuenta fue eliminada. ¡Gracias por ayudar a las mascotas!", "info")
    return redirect(url_for("Pagina_Principal"))
