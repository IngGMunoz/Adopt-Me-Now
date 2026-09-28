import io

from conftest import login
from Models.adoptar_mascotas import adoptar_mascotas
from Models.mascotas import Mascota

PAGINAS_PUBLICAS = ["/", "/adopcion", "/fundaciones", "/iniciar-sesion", "/registro"]


def test_paginas_publicas_cargan(client, destacadas):
    fichas = [f"/mascota/{m.id}" for m in Mascota.query.all()]
    assert len(fichas) == 3
    for url in PAGINAS_PUBLICAS + fichas:
        assert client.get(url).status_code == 200, url
    assert client.get("/mascota/999").status_code == 404


def test_formulario_requiere_sesion(client):
    res = client.get("/formulario")
    assert res.status_code == 302
    assert "next=/formulario" in res.headers["Location"]


def test_solicitud_de_adopcion_se_guarda(client, user):
    login(client, "ana", "secreta123")
    res = client.post(
        "/formulario?pet=Michi",
        data={"nombre": "Ana Pérez", "email": "ana@example.com", "motivo": "Tengo espacio y tiempo"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res.status_code == 201

    solicitud = adoptar_mascotas.query.one()
    assert solicitud.pet_name == "Michi"
    assert solicitud.adopter_id == user.id


def test_solicitud_incompleta_es_rechazada(client, user):
    login(client, "ana", "secreta123")
    res = client.post("/formulario", data={"nombre": ""}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert res.status_code == 400


def test_admin_publica_mascota_y_aparece_en_adopcion(client, admin_user):
    login(client, "root", "adminpass123")
    res = client.post(
        "/api/admin/mascotas",
        data={"nombre": "Toby", "descripcion": "Juguetón", "imagen": (io.BytesIO(b"img"), "toby.png")},
        content_type="multipart/form-data",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res.status_code == 201
    mascota = Mascota.query.one()
    assert mascota.autor == "root"
    assert mascota.imagen.endswith("_toby.png")

    assert b"Toby" in client.get("/adopcion").data


def test_mascota_adoptada_no_se_lista(client, admin_user):
    login(client, "root", "adminpass123")
    client.post("/api/admin/mascotas", json={"nombre": "Luna", "descripcion": "Tranquila"})
    mascota = Mascota.query.one()
    assert client.post(f"/api/admin/mascotas/{mascota.id}/adopt").status_code == 200
    assert b"Luna" not in client.get("/adopcion").data


def test_formulario_html_redirige_con_mensaje(client, user):
    # Un envío normal del navegador (Accept: */*) debe redirigir, no devolver JSON
    login(client, "ana", "secreta123")
    res = client.post(
        "/formulario?pet=Michi",
        data={"nombre": "Ana", "email": "ana@example.com"},
        headers={"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
    )
    assert res.status_code == 302
    assert res.headers["Location"] == "/adopcion"
