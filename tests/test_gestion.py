"""Gestión de usuarios y administradores desde el panel de la fundación."""

from conftest import login
from Config.db import db
from Models.admins import admin
from Models.usuario import usuario


def crear_admin(username="maria", activo=True):
    a = admin(username=username, email=f"{username}@fundacion.org", active=activo)
    a.set_password("adminpass123")
    db.session.add(a)
    db.session.commit()
    return a


def test_panel_muestra_usuarios_y_administradores(client, admin_user, user):
    login(client, "root", "adminpass123")
    pagina = client.get("/postularADM").get_data(as_text=True)
    assert 'id="panel-usuarios"' in pagina and 'id="panel-administradores"' in pagina
    assert "ana@example.com" in pagina
    assert "root@example.com" in pagina


def test_ficha_de_usuario_con_su_actividad(client, admin_user, user):
    login(client, "ana", "secreta123")
    client.post("/postular", data={"nombre": "Canela"})

    login(client, "root", "adminpass123")
    res = client.get(f"/postularADM/usuarios/{user.id}")
    assert res.status_code == 200
    pagina = res.get_data(as_text=True)
    assert "Ficha de usuario" in pagina
    assert "Postulaste a Canela para darla en adopción" in pagina


def test_ficha_de_usuario_solo_para_administradores(client, user):
    assert client.get(f"/postularADM/usuarios/{user.id}").status_code == 302
    login(client, "ana", "secreta123")
    res = client.get(f"/postularADM/usuarios/{user.id}")
    assert res.status_code == 302
    assert "/iniciar-sesion" in res.headers["Location"]


def test_admin_crea_otro_admin_sin_codigo(client, admin_user):
    login(client, "root", "adminpass123")
    res = client.post("/api/admin/admins", json={"username": "maria", "email": "maria@fundacion.org", "password": "clave-segura"})
    assert res.status_code == 201
    assert admin.query.filter_by(username="maria").one().active


def test_no_puede_desactivarse_a_si_mismo(client, admin_user):
    login(client, "root", "adminpass123")
    res = client.put(f"/api/admin/admins/{admin_user.id}", json={"active": False})
    assert res.status_code == 400
    assert db.session.get(admin, admin_user.id).active


def test_active_en_texto_se_interpreta_bien(client, admin_user):
    maria = crear_admin()
    login(client, "root", "adminpass123")
    client.put(f"/api/admin/admins/{maria.id}", json={"active": "false"})
    assert db.session.get(admin, maria.id).active is False


def test_desactivar_admin_le_quita_el_acceso_de_inmediato(app, admin_user):
    maria = crear_admin()
    sesion_maria = app.test_client()
    sesion_root = app.test_client()
    login(sesion_maria, "maria", "adminpass123")
    assert sesion_maria.get("/api/admin/users").status_code == 200

    login(sesion_root, "root", "adminpass123")
    assert sesion_root.put(f"/api/admin/admins/{maria.id}", json={"active": False}).status_code == 200

    # Su sesión abierta deja de servir y tampoco puede volver a entrar
    assert sesion_maria.get("/api/admin/users").status_code == 401
    assert login(sesion_maria, "maria", "adminpass123").status_code == 403

    # Al reactivarla puede volver a entrar
    sesion_root.put(f"/api/admin/admins/{maria.id}", json={"active": True})
    assert login(sesion_maria, "maria", "adminpass123").status_code == 200


def test_eliminar_usuario_cierra_su_sesion(app, admin_user, user):
    sesion_ana = app.test_client()
    sesion_root = app.test_client()
    login(sesion_ana, "ana", "secreta123")
    assert sesion_ana.get("/mi-cuenta/").status_code == 200

    login(sesion_root, "root", "adminpass123")
    assert sesion_root.delete(f"/api/admin/users/{user.id}").status_code == 204
    assert db.session.get(usuario, user.id) is None

    assert sesion_ana.get("/mi-cuenta/").status_code == 302
    assert sesion_ana.get("/formulario").status_code == 302
