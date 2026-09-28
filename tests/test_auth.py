from conftest import login
from Models.admins import admin


def test_registro_y_login_de_usuario(client):
    res = client.post("/api/users/register", json={"username": "luis", "email": "luis@example.com", "password": "clave1234"})
    assert res.status_code == 201
    assert "password_hash" not in res.get_json()

    res = login(client, "luis@example.com", "clave1234")
    assert res.status_code == 200
    assert res.get_json()["redirect"] == "/"


def test_registro_duplicado(client, user):
    res = client.post("/api/users/register", json={"username": "ana", "email": "otra@example.com", "password": "x" * 8})
    assert res.status_code == 409


def test_login_con_contrasena_incorrecta(client, user):
    assert login(client, "ana", "incorrecta").status_code == 401


def test_login_admin_redirige_al_panel(client, admin_user):
    res = login(client, "root", "adminpass123")
    assert res.status_code == 200
    assert res.get_json()["redirect"] == "/postularADM"


def test_login_formulario_ignora_next_externo(client, user):
    res = client.post(
        "/iniciar-sesion?next=//sitio-malicioso.com",
        data={"email": "ana", "password": "secreta123"},
    )
    assert res.status_code == 302
    assert res.headers["Location"] == "/"


def test_login_formulario_respeta_next_interno(client, user):
    res = client.post("/iniciar-sesion?next=/formulario", data={"email": "ana", "password": "secreta123"})
    assert res.headers["Location"] == "/formulario"


def test_registro_admin_requiere_codigo(client):
    datos = {"username": "nuevo", "email": "nuevo@example.com", "password": "clave-segura"}
    assert client.post("/api/admin/admins", json=datos).status_code == 403
    assert client.post("/api/admin/admins", json={**datos, "codigo": "incorrecto"}).status_code == 403

    res = client.post("/api/admin/admins", json={**datos, "codigo": "codigo-test", "role": "superadmin"})
    assert res.status_code == 201
    # sin sesión de admin no se puede elegir el rol
    assert admin.query.filter_by(username="nuevo").one().role == "admin"
