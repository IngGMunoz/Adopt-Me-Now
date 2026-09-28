"""Mascotas destacadas gestionadas desde el panel y filtros del catálogo."""

from conftest import login
from Config.db import db
from Config.schema import init_db
from Models.mascotas import Mascota
from Models.postular_mascotas import PostularMascotas


def test_destacadas_iniciales_se_cargan_una_sola_vez(app):
    db.drop_all()
    init_db()
    assert {m.nombre for m in Mascota.query.filter_by(destacada=True)} == {"Cachorro", "Michi", "Rocky"}

    # Si el administrador elimina una, no reaparece al reiniciar la app
    db.session.delete(Mascota.query.filter_by(nombre="Rocky").one())
    db.session.commit()
    init_db()
    assert Mascota.query.count() == 2


def test_destacadas_aparecen_primero(client, destacadas):
    db.session.add(Mascota(nombre="Nueva", descripcion="Recién publicada", imagen="", autor="root"))
    db.session.commit()
    pagina = client.get("/").get_data(as_text=True)
    assert "Nueva" not in pagina  # el inicio muestra tres: las destacadas ocupan los lugares
    assert "Conocer a Michi" in pagina


def test_ficha_muestra_datos_y_parrafos(client, destacadas):
    michi = Mascota.query.filter_by(nombre="Michi").one()
    pagina = client.get(f"/mascota/{michi.id}").get_data(as_text=True)
    assert "Criolla" in pagina and "8 meses" in pagina
    assert "Salud: vacunada, desparasitada y esterilizada." in pagina


def test_catalogo_incluye_datos_para_filtrar(client, destacadas):
    pagina = client.get("/adopcion").get_data(as_text=True)
    assert 'data-especie="gato"' in pagina and 'data-tamanio="pequeño"' in pagina
    assert '<option value="Barranquilla, Atlántico">' in pagina


def test_panel_publica_con_filtros_y_destacada(client, admin_user):
    login(client, "root", "adminpass123")
    client.post("/postularADM", data={
        "nombre": "Luna", "descripcion": "Perrita tranquila y cariñosa", "especie": "perro",
        "tamanio": "mediano", "ubicacion": "Soledad", "destacada": "1",
    })
    luna = Mascota.query.one()
    assert (luna.especie, luna.tamanio, luna.ubicacion, luna.destacada) == ("perro", "mediano", "Soledad", True)


def test_panel_quita_y_pone_destacada(client, admin_user, destacadas):
    michi = Mascota.query.filter_by(nombre="Michi").one()
    login(client, "root", "adminpass123")
    assert client.put(f"/api/admin/mascotas/{michi.id}", json={"destacada": "false"}).status_code == 200
    assert db.session.get(Mascota, michi.id).destacada is False
    client.put(f"/api/admin/mascotas/{michi.id}", json={"destacada": True})
    assert db.session.get(Mascota, michi.id).destacada is True


def test_aprobar_postulacion_conserva_datos_para_filtrar(client, user, admin_user):
    login(client, "ana", "secreta123")
    client.post("/postular", data={"nombre": "Canela", "especie": "gato", "tamaño": "pequeño", "ubicacion": "Malambo"})
    login(client, "root", "adminpass123")
    client.post(f"/api/admin/postulares/{PostularMascotas.query.one().id}/aprobar")
    canela = Mascota.query.one()
    assert (canela.especie, canela.tamanio, canela.ubicacion) == ("gato", "pequeño", "Malambo")
