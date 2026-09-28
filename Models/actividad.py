from datetime import datetime
from Config.db import db


class Actividad(db.Model):
    """Historial de acciones de un usuario (y de lo que las fundaciones hacen con sus solicitudes)."""

    __tablename__ = "actividad_usuario"

    # tipo -> (icono de Font Awesome, etiqueta para mostrar)
    TIPOS = {
        "registro": ("fa-user-plus", "Cuenta creada"),
        "inicio_sesion": ("fa-right-to-bracket", "Inicio de sesión"),
        "solicitud_enviada": ("fa-envelope-open-text", "Solicitud de adopción"),
        "solicitud_aprobada": ("fa-circle-check", "Solicitud aprobada"),
        "postulacion_enviada": ("fa-bullhorn", "Postulación de mascota"),
        "postulacion_publicada": ("fa-paw", "Mascota publicada"),
        "postulacion_descartada": ("fa-circle-xmark", "Postulación descartada"),
        "perfil_actualizado": ("fa-user-pen", "Perfil actualizado"),
        "contrasena_cambiada": ("fa-key", "Contraseña cambiada"),
    }

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo = db.Column(db.String(40), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    # Página relacionada (p. ej. el perfil de la mascota), opcional
    enlace = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    usuario = db.relationship("usuario", back_populates="actividades")

    @property
    def icono(self):
        return self.TIPOS.get(self.tipo, ("fa-circle", ""))[0]

    @property
    def etiqueta(self):
        return self.TIPOS.get(self.tipo, ("", self.tipo))[1]

    def __repr__(self):
        return f"<Actividad {self.id} {self.tipo} usuario={self.usuario_id}>"
