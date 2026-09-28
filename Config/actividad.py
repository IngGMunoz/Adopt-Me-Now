"""Registro del historial de actividad de los usuarios."""

from Config.db import app, db
from Models.actividad import Actividad


def registrar(usuario_id, tipo, descripcion, enlace=None, commit=True):
    """Agrega un evento al historial del usuario.

    Con commit=False el evento se guarda en la misma transacción que la acción principal.
    Si falla, se registra en el log pero nunca interrumpe la acción del usuario.
    """
    if not usuario_id:
        return
    try:
        db.session.add(Actividad(usuario_id=usuario_id, tipo=tipo, descripcion=descripcion[:255], enlace=enlace))
        if commit:
            db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("No se pudo registrar la actividad %s del usuario %s", tipo, usuario_id)


def notificar_postulacion_descartada(p):
    """Avisa al usuario en su historial cuando la fundación descarta su postulación pendiente."""
    if p.usuario_id and not p.aprobada:
        registrar(p.usuario_id, "postulacion_descartada",
                  f"La fundación revisó y descartó tu postulación de {p.nombre or 'una mascota'}", commit=False)
