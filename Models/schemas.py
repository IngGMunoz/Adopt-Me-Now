"""Schemas de Marshmallow para serializar los modelos en la API.

Viven en un módulo aparte porque al definirlos SQLAlchemy resuelve las relaciones
entre modelos: todos los modelos deben estar importados antes.
"""

from Config.db import ma
from Models.admins import admin
from Models.usuario import usuario
from Models.mascotas import Mascota
from Models.postular_mascotas import PostularMascotas
from Models.adoptar_mascotas import adoptar_mascotas  # noqa: F401  (registra el modelo para las relaciones)


class adminSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = admin
        load_instance = True
        exclude = ("password_hash",)
        dump_only = ("id", "created_at", "updated_at")


class usuarioSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = usuario
        load_instance = True
        exclude = ("password_hash",)
        dump_only = ("id", "created_at", "updated_at")


class MascotaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mascota
        load_instance = True
        include_fk = True


class PostularMascotasSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PostularMascotas
        load_instance = True
        include_fk = True
