from datetime import datetime

from flask import url_for

from Config.db import db


class Mascota(db.Model):
    __tablename__ = "mascotas"

    # Campos opcionales que llegan igual desde el panel, la API y las postulaciones
    CAMPOS = ("especie", "raza", "edad", "sexo", "tamanio", "ubicacion")

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(140), nullable=False, index=True)
    descripcion = db.Column(db.Text, nullable=False)
    imagen = db.Column(db.String(300), nullable=False)  # nombre/URL del archivo en static/uploads
    autor = db.Column(db.String(120), nullable=False)   # nombre visible de quien publica (admin o fundación)
    is_adopted = db.Column(db.Boolean, default=False, nullable=False)
    # Se muestra primero en el inicio y en el catálogo; el administrador la marca desde el panel
    destacada = db.Column(db.Boolean, default=False, nullable=False)
    # Datos para los filtros del catálogo y la ficha (especie y tamaño en minúsculas: perro, pequeño…)
    especie = db.Column(db.String(60), nullable=True)
    raza = db.Column(db.String(120), nullable=True)
    edad = db.Column(db.String(60), nullable=True)
    sexo = db.Column(db.String(20), nullable=True)
    tamanio = db.Column(db.String(40), nullable=True)
    ubicacion = db.Column(db.String(200), nullable=True)
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

    @property
    def imagen_url(self):
        """Las fotos subidas están en static/uploads; las iniciales, en static/images."""
        if not self.imagen:
            return url_for("static", filename="images/Perro.jpg")
        return url_for("static", filename=self.imagen if "/" in self.imagen else "uploads/" + self.imagen)

    def __repr__(self):
        return f"<Mascota {self.id} {self.nombre}>"
