"""Blueprint de adopciones API.

IMPORTANTE: No manejar el formulario HTML en este blueprint para evitar colisiones
con la ruta '/formulario' de `app.py` que incluye autenticación y lógica de flashes.

Este blueprint queda solo para endpoints futuros tipo API (/adopciones/*).
"""

from flask import Blueprint, jsonify

Routes_adoptarC = Blueprint("Routes_adoptarC", __name__, url_prefix="/adopciones")

@Routes_adoptarC.route("/ping")
def ping_adopciones():
    return jsonify({"ok": True, "service": "adopciones", "status": "ready"})