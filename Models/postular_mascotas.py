from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from Config.db import ma, db, app

class PostularMascotas(db.Model):
    __tablename__ = "postular_mascotas"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PostularMascotas {self.id} {self.username}>"

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
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