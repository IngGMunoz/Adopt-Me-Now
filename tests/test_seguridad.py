"""CSRF, límite de intentos de inicio de sesión y avisos por correo."""

from conftest import login
from Config import actividad
from Models.adoptar_mascotas import adoptar_mascotas
from Models.usuario import usuario

REGISTRO = {"nombre": "luis", "email": "luis@example.com", "password": "clave1234"}


def token(client, pagina="/registro"):
    client.get(pagina)
    with client.session_transaction() as s:
        return s["csrf_token"]


def test_csrf_rechaza_formulario_sin_token(app, client):
    app.config["CSRF_ENABLED"] = True
    client.post("/registro", data=REGISTRO)
    assert usuario.query.count() == 0

    client.post("/registro", data={**REGISTRO, "csrf_token": token(client)})
    assert usuario.query.count() == 1


def test_csrf_en_fetch_via_cabecera(app, client, admin_user, user):
    app.config["CSRF_ENABLED"] = True
    login(client, "root", "adminpass123")  # JSON: exento, el navegador no lo envía entre sitios
    assert client.delete(f"/api/admin/users/{user.id}").status_code == 400
    res = client.delete(f"/api/admin/users/{user.id}", headers={"X-CSRF-Token": token(client, "/postularADM")})
    assert res.status_code == 204


def test_login_se_bloquea_tras_cinco_fallos(client, user):
    for _ in range(5):
        client.post("/iniciar-sesion", data={"email": "ana", "password": "incorrecta"})
    # Ni con la contraseña correcta, ni por la página ni por la API
    assert client.post("/iniciar-sesion", data={"email": "ana", "password": "secreta123"}).status_code == 429
    assert login(client, "ana", "secreta123").status_code == 429


def test_login_exitoso_reinicia_el_contador(client, user):
    for _ in range(4):
        login(client, "ana", "incorrecta")
    assert login(client, "ana", "secreta123").status_code == 200
    for _ in range(4):
        login(client, "ana", "incorrecta")
    assert login(client, "ana", "secreta123").status_code == 200


class SMTPFalso:
    enviados = []

    def __init__(self, host, port, timeout):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def starttls(self):
        pass

    def login(self, usuario, clave):
        pass

    def send_message(self, msg):
        self.enviados.append(msg)


class HiloInmediato:
    def __init__(self, target, daemon):
        self.target = target

    def start(self):
        self.target()


def test_correo_al_aprobar_una_solicitud(monkeypatch, client, user, admin_user):
    SMTPFalso.enviados.clear()
    monkeypatch.setenv("SMTP_HOST", "smtp.prueba")
    monkeypatch.setattr(actividad.smtplib, "SMTP", SMTPFalso)
    monkeypatch.setattr(actividad.threading, "Thread", HiloInmediato)

    login(client, "ana", "secreta123")
    client.post("/formulario?pet=Michi", data={"nombre": "Ana", "email": "ana.contacto@example.com"},
                headers={"X-Requested-With": "XMLHttpRequest"})
    login(client, "root", "adminpass123")
    client.post(f"/api/admin/solicitudes/{adoptar_mascotas.query.one().id}/confirmar")

    [correo] = SMTPFalso.enviados
    assert correo["To"] == "ana.contacto@example.com"
    assert correo["Subject"] == "Tu solicitud de adopción fue aprobada"
    assert "Michi" in correo.get_content()


def test_sin_smtp_no_se_envian_correos(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    assert actividad.enviar_correo("ana@example.com", "Asunto", "Texto") is None


def test_demo_crea_cuentas_de_prueba_con_datos(client, destacadas):
    from Config.demo import sembrar_demo
    sembrar_demo()
    sembrar_demo()  # idempotente
    assert usuario.query.count() == 1
    assert adoptar_mascotas.query.one().mascota.nombre == "Michi"
    assert login(client, "fundacion@demo.com", "DemoFundacion1").status_code == 200
    assert login(client, "adoptante@demo.com", "DemoAdoptante1").status_code == 200


def test_demo_protege_las_cuentas_de_prueba(app, client, destacadas):
    from Config.demo import sembrar_demo
    from Models.admins import admin
    sembrar_demo()
    app.config["DEMO_MODE"] = True
    fundacion = admin.query.filter_by(email="fundacion@demo.com").one()
    adoptante = usuario.query.filter_by(email="adoptante@demo.com").one()

    # Ni la fundación de prueba ni un admin creado por un visitante pueden tocarlas
    login(client, "fundacion@demo.com", "DemoFundacion1")
    client.post("/api/admin/admins", json={"username": "visitante", "email": "v@x.com", "password": "clave-visitante"})
    login(client, "visitante", "clave-visitante")
    assert client.put(f"/api/admin/admins/{fundacion.id}", json={"active": False}).status_code == 403
    assert client.delete(f"/api/admin/users/{adoptante.id}").status_code == 403

    # El adoptante de prueba no puede cambiar su contraseña ni borrar su cuenta
    login(client, "adoptante@demo.com", "DemoAdoptante1")
    client.post("/mi-cuenta/contrasena", data={"actual": "DemoAdoptante1", "nueva": "otra-clave-123", "confirmacion": "otra-clave-123"})
    client.post("/mi-cuenta/eliminar", data={"password": "DemoAdoptante1"})
    assert login(client, "adoptante@demo.com", "DemoAdoptante1").status_code == 200

    # Una cuenta creada por un visitante sí se puede eliminar
    client.post("/registro", data=REGISTRO)
    luis = usuario.query.filter_by(username="luis").one()
    login(client, "visitante", "clave-visitante")
    assert client.delete(f"/api/admin/users/{luis.id}").status_code == 204
