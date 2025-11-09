from Config.db import db

class adoptar_mascotas(db.Model):
    __tablename__ = "adoptar_mascotas"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    ocupacion = db.Column(db.String(100), nullable=True)
    vivienda = db.Column(db.String(50), nullable=True)
    tiene_mascotas = db.Column(db.String(50), nullable=True)
    motivo = db.Column(db.Text, nullable=True)
    pet_name = db.Column(db.String(100), nullable=True)
    # FK correcta hacia la tabla 'usuarios'
    adopter_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    is_confirmed = db.Column(db.Boolean, default=False)

    def __init__(self, username, email, telefono, direccion, ocupacion, vivienda, tiene_mascotas, motivo, pet_name, adopter_id=None):
        self.username = username
        self.email = email
        self.telefono = telefono
        self.direccion = direccion
        self.ocupacion = ocupacion
        self.vivienda = vivienda
        self.tiene_mascotas = tiene_mascotas
        self.motivo = motivo
        self.pet_name = pet_name
        self.adopter_id = adopter_id
