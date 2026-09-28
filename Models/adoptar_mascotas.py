from datetime import datetime
from Config.db import db


class adoptar_mascotas(db.Model):
    """Solicitud de adopción: un usuario (adoptante) pide adoptar una mascota publicada."""

    __tablename__ = "adoptar_mascotas"

    id = db.Column(db.Integer, primary_key=True)
    # Datos de contacto que el adoptante escribe en el formulario
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    ocupacion = db.Column(db.String(100), nullable=True)
    vivienda = db.Column(db.String(50), nullable=True)
    tiene_mascotas = db.Column(db.String(50), nullable=True)
    motivo = db.Column(db.Text, nullable=True)
    # Nombre de la mascota tal como se pidió (las páginas fijas como /michi no están en la tabla mascotas)
    pet_name = db.Column(db.String(100), nullable=True)

    adopter_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    mascota_id = db.Column(
        db.Integer, db.ForeignKey("mascotas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    adoptante = db.relationship("usuario", back_populates="solicitudes")
    mascota = db.relationship("Mascota", back_populates="solicitudes")

    def __repr__(self):
        return f"<adoptar_mascotas {self.id} {self.username} -> {self.pet_name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "telefono": self.telefono,
            "direccion": self.direccion,
            "ocupacion": self.ocupacion,
            "vivienda": self.vivienda,
            "tiene_mascotas": self.tiene_mascotas,
            "motivo": self.motivo,
            "pet_name": self.mascota.nombre if self.mascota else self.pet_name,
            "adopter_id": self.adopter_id,
            "adoptante": self.adoptante.username if self.adoptante else None,
            "mascota_id": self.mascota_id,
            "is_confirmed": self.is_confirmed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
