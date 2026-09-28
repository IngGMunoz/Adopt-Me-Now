from conftest import login
from Config.db import db
from Models.adoptar_mascotas import adoptar_mascotas
from Models.mascotas import Mascota
from Models.postular_mascotas import PostularMascotas


def publicar(client, nombre="Luna"):
    res = client.post("/api/admin/mascotas", json={"nombre": nombre, "descripcion": "Tranquila"})
    assert res.status_code == 201
    return Mascota.query.filter_by(nombre=nombre).one()


def test_mascota_queda_enlazada_al_admin_que_la_publica(client, admin_user):
    login(client, "root", "adminpass123")
    mascota = publicar(client)
    assert mascota.publicado_por is admin_user
    assert admin_user.mascotas_publicadas == [mascota]
    # ya no se crea la fila "espejo" en postular_mascotas
    assert PostularMascotas.query.count() == 0


def test_solicitud_enlaza_adoptante_y_mascota(client, admin_user, user):
    login(client, "root", "adminpass123")
    mascota = publicar(client)
    mascota_id = mascota.id

    login(client, "ana", "secreta123")
    res = client.post(
        f"/formulario?mascota={mascota_id}",
        data={"nombre": "Ana", "email": "ana@example.com"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res.status_code == 201

    solicitud = adoptar_mascotas.query.one()
    assert solicitud.mascota.id == mascota_id
    assert solicitud.adoptante is user
    assert solicitud.pet_name == "Luna"
    assert user.solicitudes == [solicitud]


def test_solicitud_por_nombre_se_enlaza_si_la_mascota_existe(client, admin_user, user):
    login(client, "root", "adminpass123")
    mascota = publicar(client, "Rocky")

    login(client, "ana", "secreta123")
    client.post("/formulario?pet=Rocky", data={"nombre": "Ana", "email": "ana@example.com"},
                headers={"X-Requested-With": "XMLHttpRequest"})
    assert adoptar_mascotas.query.one().mascota_id == mascota.id


def test_confirmar_solicitud_marca_la_mascota_como_adoptada(client, admin_user, user):
    login(client, "root", "adminpass123")
    mascota = publicar(client)
    mascota_id = mascota.id

    login(client, "ana", "secreta123")
    client.post(f"/formulario?mascota={mascota_id}", data={"nombre": "Ana", "email": "ana@example.com"},
                headers={"X-Requested-With": "XMLHttpRequest"})
    solicitud_id = adoptar_mascotas.query.one().id

    login(client, "root", "adminpass123")
    listado = client.get(f"/api/admin/solicitudes?mascota_id={mascota_id}").get_json()
    assert [s["adoptante"] for s in listado] == ["ana"]

    assert client.post(f"/api/admin/solicitudes/{solicitud_id}/confirmar").status_code == 200
    assert db.session.get(Mascota, mascota_id).is_adopted
    assert b"Luna" not in client.get("/adopcion").data

    # una mascota adoptada ya no acepta solicitudes nuevas
    login(client, "ana", "secreta123")
    res = client.post(f"/formulario?mascota={mascota_id}", data={"nombre": "Ana", "email": "ana@example.com"},
                      headers={"X-Requested-With": "XMLHttpRequest"})
    assert res.status_code == 409


def test_postulacion_enlaza_usuario_y_al_aprobarla_crea_la_mascota(client, admin_user, user):
    login(client, "ana", "secreta123")
    client.post("/postular", data={"nombre": "Canela", "especie": "Perro", "edad": "3 años"})
    postulacion = PostularMascotas.query.one()
    assert postulacion.usuario is user
    assert not postulacion.aprobada

    login(client, "root", "adminpass123")
    res = client.post(f"/api/admin/postulares/{postulacion.id}/aprobar")
    assert res.status_code == 201

    postulacion = db.session.get(PostularMascotas, postulacion.id)
    assert postulacion.aprobada
    assert postulacion.mascota.nombre == "Canela"
    assert "Especie: Perro" in postulacion.mascota.descripcion
    assert postulacion.mascota.publicado_por is admin_user
    assert client.post(f"/api/admin/postulares/{postulacion.id}/aprobar").status_code == 409


def test_borrar_usuario_conserva_sus_solicitudes(client, admin_user, user):
    login(client, "ana", "secreta123")
    client.post("/formulario?pet=Michi", data={"nombre": "Ana", "email": "ana@example.com"},
                headers={"X-Requested-With": "XMLHttpRequest"})

    login(client, "root", "adminpass123")
    assert client.delete(f"/api/admin/users/{user.id}").status_code == 204

    solicitud = adoptar_mascotas.query.one()
    assert solicitud.adopter_id is None
    assert solicitud.pet_name == "Michi"
