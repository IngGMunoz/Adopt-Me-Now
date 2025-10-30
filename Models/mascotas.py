
from datetime import datetime
from Config.db import ma, db, app

class Mascota(db.Model):
    __tablename__ = "mascotas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(140), nullable=False, index=True)
    descripcion = db.Column(db.Text, nullable=False)
    imagen = db.Column(db.String(300), nullable=False)  # nombre/URL del archivo en static/uploads
    autor = db.Column(db.String(120), nullable=False)   # nombre de usuario o fundación
    is_adopted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
            # Schema de Marshmallow para serialización
class MascotaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mascota
        load_instance = True

# Crear tablas automáticamente al importar el modelo
with app.app_context():
    db.create_all()