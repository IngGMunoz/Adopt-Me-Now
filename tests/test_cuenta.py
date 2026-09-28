from conftest import login
from Config.db import db
from Models.actividad import Actividad
from Models.adoptar_mascotas import adoptar_mascotas
from Models.postular_mascotas import PostularMascotas
from Models.usuario import usuario


def tipos(usuario_id):
    return [a.tipo for a in Actividad.query.filter_by(usuario_id=usuario_id).order_by(Actividad.id)]


def test_mi_cuenta_requiere_sesion(client):
    res = client.get("/mi-cuenta/")
    assert res.status_code == 302
    assert "/iniciar-sesion" in res.headers["Location"]


def test_admin_es_enviado_a_su_panel(client, admin_user):
    login(client, "root", "adminpass123")
    res = client.get("/mi-cuenta/")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/postularADM")


def test_registro_e_inicio_de_sesion_quedan_en_la_actividad(client):
    client.post("/registro", data={"nombre": "luis", "email": "luis@example.com", "password": "clave1234"})
    client.post("/iniciar-sesion", data={"email": "luis", "password": "clave1234"})
    u = usuario.query.filter_by(username="luis").one()
    assert tipos(u.id) == ["registro", "inicio_sesion"]

    pagina = client.get("/mi-cuenta/").get_data(as_text=True)
    assert "Creaste tu cuenta en Adopt Me" in pagina
    assert "Iniciaste sesión" in pagina


def test_solicitud_y_postulacion_quedan_en_la_actividad(client, user):
    login(client, "ana", "secreta123")
    client.post("/formulario?pet=Michi", data={"nombre": "Ana", "email": "ana@example.com"},
                headers={"X-Requested-With": "XMLHttpRequest"})
    client.post("/postular", data={"nombre": "Canela", "especie": "perro"})

    assert tipos(user.id)[-2:] == ["solicitud_enviada", "postulacion_enviada"]
    solicitud = Actividad.query.filter_by(usuario_id=user.id, tipo="solicitud_enviada").one()
    assert solicitud.descripcion == "Enviaste una solicitud para adoptar a Michi"
    assert solicitud.enlace == "/michi"

    pagina = client.get("/mi-cuenta/").get_data(as_text=True)
    assert "Postulaste a Canela para darla en adopción" in pagina


def test_decisiones_de_la_fundacion_llegan_al_historial(client, user, admin_user):
    login(client, "ana", "secreta123")
    client.post("/formulario?pet=Michi", data={"nombre": "Ana", "email": "ana@example.com"},
                headers={"X-Requested-With": "XMLHttpRequest"})
    client.post("/postular", data={"nombre": "Canela"})
    client.post("/postular", data={"nombre": "Bruno"})
    solicitud = adoptar_mascotas.query.one()
    canela = PostularMascotas.query.filter_by(nombre="Canela").one()
    bruno = PostularMascotas.query.filter_by(nombre="Bruno").one()

    login(client, "root", "adminpass123")
    client.post(f"/api/admin/solicitudes/{solicitud.id}/confirmar")
    client.post(f"/api/admin/postulares/{canela.id}/aprobar")
    client.delete(f"/api/admin/postulares/{bruno.id}")

    assert tipos(user.id)[-3:] == ["solicitud_aprobada", "postulacion_publicada", "postulacion_descartada"]


def test_filtrar_actividad_por_tipo(client, user):
    login(client, "ana", "secreta123")
    client.post("/postular", data={"nombre": "Canela"})
    pagina = client.get("/mi-cuenta/?tipo=postulacion_enviada").get_data(as_text=True)
    assert "Postulaste a Canela" in pagina
    assert "Iniciaste sesión</p>" not in pagina


def test_actualizar_perfil(client, user):
    login(client, "ana", "secreta123")
    res = client.post("/mi-cuenta/perfil", data={"username": "ana.maria", "email": "ana.maria@example.com"})
    assert res.status_code == 302

    u = db.session.get(usuario, user.id)
    assert (u.username, u.email) == ("ana.maria", "ana.maria@example.com")
    assert Actividad.query.filter_by(usuario_id=user.id, tipo="perfil_actualizado").count() == 1


def test_perfil_no_acepta_datos_de_otro_usuario(client, user):
    otro = usuario(username="otro", email="otro@example.com")
    otro.set_password("x" * 8)
    db.session.add(otro)
    db.session.commit()

    login(client, "ana", "secreta123")
    client.post("/mi-cuenta/perfil", data={"username": "otro", "email": "ana@example.com"})
    assert db.session.get(usuario, user.id).username == "ana"


def test_cambiar_contrasena(client, user):
    login(client, "ana", "secreta123")

    client.post("/mi-cuenta/contrasena", data={"actual": "incorrecta", "nueva": "nuevaClave1", "confirmacion": "nuevaClave1"})
    assert db.session.get(usuario, user.id).check_password("secreta123")

    client.post("/mi-cuenta/contrasena", data={"actual": "secreta123", "nueva": "nuevaClave1", "confirmacion": "otraCosa1"})
    assert db.session.get(usuario, user.id).check_password("secreta123")

    client.post("/mi-cuenta/contrasena", data={"actual": "secreta123", "nueva": "nuevaClave1", "confirmacion": "nuevaClave1"})
    assert db.session.get(usuario, user.id).check_password("nuevaClave1")
    assert tipos(user.id)[-1] == "contrasena_cambiada"


def test_eliminar_cuenta_borra_historial_y_conserva_solicitudes(client, user):
    login(client, "ana", "secreta123")
    client.post("/formulario?pet=Michi", data={"nombre": "Ana", "email": "ana@example.com"},
                headers={"X-Requested-With": "XMLHttpRequest"})

    client.post("/mi-cuenta/eliminar", data={"password": "mala"})
    assert db.session.get(usuario, user.id) is not None

    res = client.post("/mi-cuenta/eliminar", data={"password": "secreta123"})
    assert res.status_code == 302
    assert db.session.get(usuario, user.id) is None
    assert Actividad.query.count() == 0
    assert adoptar_mascotas.query.one().adopter_id is None
    # la sesión se cerró
    assert client.get("/mi-cuenta/").status_code == 302
