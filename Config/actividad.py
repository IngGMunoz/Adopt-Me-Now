"""Historial de actividad de los usuarios y avisos por correo."""

import os
import smtplib
import threading
from datetime import datetime
from email.message import EmailMessage
from itertools import groupby

from Config.db import app, db
from Config.filtros import TZ_OFFSET, fecha
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


def agrupar_por_dia(actividades):
    """[("Hoy", [...]), ("Ayer", [...]), ("25 sep 2026", [...])] en hora local."""
    hoy = (datetime.utcnow() + TZ_OFFSET).date()
    grupos = []
    for dia, items in groupby(actividades, key=lambda a: (a.created_at + TZ_OFFSET).date()):
        dias = (hoy - dia).days
        titulo = "Hoy" if dias == 0 else "Ayer" if dias == 1 else fecha(datetime.combine(dia, datetime.min.time()) - TZ_OFFSET, con_hora=False)
        grupos.append((titulo, list(items)))
    return grupos


def enviar_correo(destino, asunto, texto):
    """Envía un correo en segundo plano por SMTP (STARTTLS). Sin SMTP_HOST en .env no hace nada.

    Devuelve el hilo del envío (o None) para poder esperarlo en los tests.
    """
    host = os.getenv("SMTP_HOST")
    if not host or not destino:
        return None
    usuario, clave = os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", "")
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM") or usuario
    msg["To"] = destino
    msg["Subject"] = asunto
    msg.set_content(f"{texto}\n\nEquipo de Adopt Me")

    def enviar():
        try:
            with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=10) as smtp:
                smtp.starttls()
                if usuario:
                    smtp.login(usuario, clave)
                smtp.send_message(msg)
        except Exception:
            app.logger.exception("No se pudo enviar el correo a %s", destino)

    hilo = threading.Thread(target=enviar, daemon=True)
    hilo.start()
    return hilo


def notificar_postulacion_descartada(p):
    """Avisa al usuario (historial y correo) cuando la fundación descarta su postulación pendiente."""
    if p.usuario_id and not p.aprobada:
        texto = f"La fundación revisó y descartó tu postulación de {p.nombre or 'una mascota'}"
        registrar(p.usuario_id, "postulacion_descartada", texto, commit=False)
        enviar_correo(p.usuario.email, "Tu postulación fue revisada", texto + ".")
