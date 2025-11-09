from datetime import datetime
from Config.db import db, app


class SolicitudAdopcion(db.Model):
    __tablename__ = "solicitudes_adopcion"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    ocupacion = db.Column(db.String(100), nullable=True)
    vivienda = db.Column(db.String(80), nullable=True)
    tiene_mascotas = db.Column(db.String(80), nullable=True)
    motivo = db.Column(db.Text, nullable=True)
    pet_name = db.Column(db.String(120), nullable=True)

    adopter_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SolicitudAdopcion id={self.id} username={self.username!r}>"


# Garantizar la creación de la tabla cuando se importe el módulo (siguiendo el patrón del proyecto)
with app.app_context():
    db.create_all()
