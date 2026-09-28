from datetime import datetime
from Config.db import db


class PostularMascotas(db.Model):
    """Mascota propuesta por un usuario desde /postular. Un admin la revisa y, si la
    aprueba, se crea la Mascota publicada y queda enlazada en `mascota_id`."""

    __tablename__ = "postular_mascotas"

    id = db.Column(db.Integer, primary_key=True)

    # Usuario que propone la mascota
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Mascota publicada a partir de esta postulación (NULL mientras está pendiente)
    mascota_id = db.Column(
        db.Integer, db.ForeignKey("mascotas.id", ondelete="SET NULL"), nullable=True, unique=True
    )

    # Campos del formulario de postular mascota
    nombre = db.Column(db.String(140), nullable=True, index=True)
    descripcion = db.Column(db.Text, nullable=True)
    especie = db.Column(db.String(60), nullable=True)
    raza = db.Column(db.String(120), nullable=True)
    edad = db.Column(db.String(60), nullable=True)
    sexo = db.Column(db.String(20), nullable=True)
    tamanio = db.Column(db.String(40), nullable=True)
    color = db.Column(db.String(60), nullable=True)
    ubicacion = db.Column(db.String(200), nullable=True)
    imagen = db.Column(db.String(300), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    usuario = db.relationship("usuario", back_populates="postulaciones")
    mascota = db.relationship("Mascota", back_populates="postulacion")

    @property
    def aprobada(self):
        return self.mascota_id is not None

    def __repr__(self):
        return f"<PostularMascotas {self.id} {self.nombre}>"

    def descripcion_publica(self):
        """Arma la descripción de la mascota publicada a partir de los datos de la postulación."""
        if self.descripcion:
            return self.descripcion
        detalles = [
            ("Especie", self.especie), ("Raza", self.raza), ("Edad", self.edad), ("Sexo", self.sexo),
            ("Tamaño", self.tamanio), ("Color", self.color), ("Ubicación", self.ubicacion),
        ]
        return ". ".join(f"{k}: {v}" for k, v in detalles if v) or "Sin descripción"
