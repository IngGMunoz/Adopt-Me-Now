from datetime import datetime
from Config.db import db

class Mascota(db.Model):
    __tablename__ = "mascotas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(140), nullable=False, index=True)
    descripcion = db.Column(db.Text, nullable=False)
    imagen = db.Column(db.String(300), nullable=False)  # nombre/URL del archivo en static/uploads
    autor = db.Column(db.String(120), nullable=False)   # nombre visible de quien publica (admin o fundación)
    is_adopted = db.Column(db.Boolean, default=False, nullable=False)
    # Administrador que publicó la mascota
    publicado_por_id = db.Column(
        db.Integer, db.ForeignKey("admins.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    publicado_por = db.relationship("admin", back_populates="mascotas_publicadas")
    solicitudes = db.relationship("adoptar_mascotas", back_populates="mascota")
    # Postulación de usuario de la que salió esta mascota (si fue aprobada desde /postular)
    postulacion = db.relationship("PostularMascotas", back_populates="mascota", uselist=False)

    def __repr__(self):
        return f"<Mascota {self.id} {self.nombre}>"

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "imagen": self.imagen,
            "autor": self.autor,
            "is_adopted": self.is_adopted,
            "publicado_por_id": self.publicado_por_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
