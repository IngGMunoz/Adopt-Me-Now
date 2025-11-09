from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from Config.db import ma, db, app


class PostularMascotas(db.Model):
    __tablename__ = "postular_mascotas"

    id = db.Column(db.Integer, primary_key=True)

    # Campos legacy (opcional, para compatibilidad con API existente)
    username = db.Column(db.String(80), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=False, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)

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

    def __repr__(self):
        return f"<PostularMascotas {self.id} {self.nombre or self.username}>"

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "nombre": self.nombre,
            "especie": self.especie,
            "raza": self.raza,
            "edad": self.edad,
            "sexo": self.sexo,
            "tamanio": self.tamanio,
            "color": self.color,
            "ubicacion": self.ubicacion,
            "imagen": self.imagen,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Schema de Marshmallow para serialización
class PostularMascotasSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PostularMascotas
        load_instance = True
        exclude = ("password_hash",)  # evita exponer el hash en las respuestas


# Crear tablas automáticamente al importar el modelo (dev)
with app.app_context():
    db.create_all()