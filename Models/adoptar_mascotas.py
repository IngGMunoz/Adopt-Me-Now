from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from Config.db import ma, db, app

class adoptar_mascotas(db.Model):
    __tablename__ = "adoptar_mascotas"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=True, index=True)   # opcional, mantengo por compatibilidad
    email = db.Column(db.String(120), nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=True)

    # Nuevos campos para registrar adopciones confirmadas
    mascota_id = db.Column(db.Integer, db.ForeignKey("mascotas.id"), nullable=True)
    adopter_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    adoption_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones (usar string names para evitar import cycles)
    adopter = db.relationship("usuario", backref=db.backref("adoptions", lazy="dynamic"), foreign_keys=[adopter_id])
    mascota = db.relationship("Mascota", backref=db.backref("adoptions", lazy="dynamic"), foreign_keys=[mascota_id])

    def __repr__(self):
        return f"<adoptar_mascotas {self.id} adopter={self.adopter_id} mascota={self.mascota_id}>"

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "mascota_id": self.mascota_id,
            "adopter_id": self.adopter_id,
            "adoption_date": self.adoption_date.isoformat() if self.adoption_date else None,
            "is_confirmed": bool(self.is_confirmed),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # info adicional si las relaciones están cargadas
            "mascota": {"id": self.mascota.id, "nombre": getattr(self.mascota, "nombre", None)} if self.mascota else None,
            "adopter": {"id": self.adopter.id, "username": getattr(self.adopter, "username", None)} if self.adopter else None,
        }

class adoptar_mascotasSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = adoptar_mascotas
        load_instance = True
        include_fk = True
        exclude = ("password_hash",)
        dump_only = ("id", "created_at", "updated_at", "adoption_date")

# Crear tablas automáticamente en desarrollo (colocado fuera de la definición de clase)
with app.app_context():
    db.create_all()