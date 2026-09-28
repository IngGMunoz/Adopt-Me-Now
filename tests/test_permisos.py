import pytest

from conftest import login

ADMIN_ENDPOINTS = [
    ("get", "/api/admin/admins"),
    ("get", "/api/admin/users"),
    ("delete", "/api/admin/users/1"),
    ("post", "/api/admin/mascotas"),
    ("get", "/api/admin/postulares"),
    ("get", "/api/users/"),
]


@pytest.mark.parametrize("method,url", ADMIN_ENDPOINTS)
def test_api_admin_rechaza_anonimos(client, method, url):
    res = getattr(client, method)(url, json={})
    assert res.status_code == 401


@pytest.mark.parametrize("method,url", ADMIN_ENDPOINTS)
def test_api_admin_rechaza_usuarios_normales(client, user, method, url):
    login(client, "ana", "secreta123")
    res = getattr(client, method)(url, json={})
    assert res.status_code == 403


def test_api_admin_permite_administradores(client, admin_user):
    login(client, "root", "adminpass123")
    assert client.get("/api/admin/users").status_code == 200


def test_panel_admin_redirige_al_login(client, user):
    res = client.get("/postularADM")
    assert res.status_code == 302
    assert "/iniciar-sesion" in res.headers["Location"]

    login(client, "ana", "secreta123")
    assert client.get("/postularADM").status_code == 302


def test_usuario_solo_accede_a_su_cuenta(client, user, app):
    from Config.db import db
    from Models.usuario import usuario

    otro = usuario(username="otro", email="otro@example.com")
    otro.set_password("x" * 8)
    db.session.add(otro)
    db.session.commit()

    login(client, "ana", "secreta123")
    assert client.get(f"/api/users/{user.id}").status_code == 200
    assert client.get(f"/api/users/{otro.id}").status_code == 403
    assert client.delete(f"/api/users/{otro.id}").status_code == 403
