"""Filtros de Jinja para mostrar fechas en español.

Las fechas se guardan en UTC; se muestran en la hora local de la app
(Colombia, UTC-5 sin horario de verano). Se puede cambiar con TZ_OFFSET_HOURS.
"""

import os
from datetime import datetime, timedelta

from Config.db import app

TZ_OFFSET = timedelta(hours=int(os.getenv("TZ_OFFSET_HOURS", "-5")))
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


@app.template_filter("fecha")
def fecha(dt, con_hora=True):
    """28 sep 2026, 11:30 a. m."""
    if not dt:
        return ""
    local = dt + TZ_OFFSET
    texto = f"{local.day} {MESES[local.month - 1]} {local.year}"
    if con_hora:
        hora = local.hour % 12 or 12
        sufijo = "a. m." if local.hour < 12 else "p. m."
        texto += f", {hora}:{local.minute:02d} {sufijo}"
    return texto


@app.template_filter("hace")
def hace(dt):
    """Tiempo relativo: 'hace 5 minutos', 'ayer', 'hace 3 días'…"""
    if not dt:
        return ""
    segundos = int((datetime.utcnow() - dt).total_seconds())
    if segundos < 60:
        return "hace un momento"
    minutos = segundos // 60
    if minutos < 60:
        return f"hace {minutos} minuto{'s' if minutos != 1 else ''}"
    horas = minutos // 60
    if horas < 24:
        return f"hace {horas} hora{'s' if horas != 1 else ''}"
    dias = horas // 24
    if dias == 1:
        return "ayer"
    if dias < 30:
        return f"hace {dias} días"
    return fecha(dt, con_hora=False)
