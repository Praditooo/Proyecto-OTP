"""Pruebas de integración: llaman a la API completa (rutas + base de datos)."""

USUARIO = {
    "email": "ana.perez@gmail.com",
    "password": "Clave1234",
    "full_name": "Ana Pérez",
}


def encabezado(token):
    """Arma el encabezado Authorization con el token JWT."""
    return {"Authorization": f"Bearer {token}"}


def iniciar_sesion(client, sent_emails):
    """Registra al usuario, hace login, lee el OTP del 'correo' y devuelve el token."""
    client.post("/auth/register", json=USUARIO)
    client.post(
        "/auth/login",
        json={"email": USUARIO["email"], "password": USUARIO["password"]},
    )
    code = sent_emails[-1]["code"]
    respuesta = client.post(
        "/auth/verify-otp", json={"email": USUARIO["email"], "code": code}
    )
    return respuesta.json()["access_token"]


def test_registro_exitoso_y_correo_duplicado(client):
    r1 = client.post("/auth/register", json=USUARIO)
    assert r1.status_code == 201
    cuerpo = r1.json()
    assert cuerpo["email"] == USUARIO["email"]
    assert "password" not in cuerpo and "password_hash" not in cuerpo

    r2 = client.post("/auth/register", json=USUARIO)
    assert r2.status_code == 409


def test_flujo_completo_login_otp_y_perfil(client, sent_emails):
    token = iniciar_sesion(client, sent_emails)

    perfil = client.get("/users/profile", headers=encabezado(token))
    assert perfil.status_code == 200
    assert perfil.json()["email"] == USUARIO["email"]

    nuevo = client.put(
        "/users/profile",
        json={"full_name": "Ana María Pérez"},
        headers=encabezado(token),
    )
    assert nuevo.status_code == 200
    assert nuevo.json()["full_name"] == "Ana María Pérez"


def test_login_con_contrasena_incorrecta_no_envia_otp(client, sent_emails):
    client.post("/auth/register", json=USUARIO)
    r = client.post(
        "/auth/login", json={"email": USUARIO["email"], "password": "Equivocada1"}
    )
    assert r.status_code == 401
    assert sent_emails == []


def test_ruta_protegida_exige_token_valido(client):
    assert client.get("/users/profile").status_code == 401
    assert client.get("/users/profile", headers=encabezado("token-falso")).status_code == 401


def test_logout_revoca_el_token(client, sent_emails):
    token = iniciar_sesion(client, sent_emails)

    salida = client.post("/auth/logout", headers=encabezado(token))
    assert salida.status_code == 200

    despues = client.get("/users/profile", headers=encabezado(token))
    assert despues.status_code == 401


def test_refresh_entrega_token_nuevo_y_revoca_el_anterior(client, sent_emails):
    viejo = iniciar_sesion(client, sent_emails)

    r = client.post("/auth/refresh", headers=encabezado(viejo))
    assert r.status_code == 200
    nuevo = r.json()["access_token"]
    assert nuevo != viejo

    assert client.get("/users/profile", headers=encabezado(viejo)).status_code == 401
    assert client.get("/users/profile", headers=encabezado(nuevo)).status_code == 200
