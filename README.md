# Sistema de autenticación con OTP (FastAPI)

API de autenticación de dos factores: el usuario inicia sesión con correo y contraseña,
recibe un código OTP de 6 dígitos por correo electrónico (válido 15 minutos) y, al
verificarlo, obtiene un token JWT para acceder a las rutas protegidas.

**URL del despliegue:** _()_
**Documentación interactiva:** `<URL>/docs`

## Tecnologías

- FastAPI (Python 3.9+) y Uvicorn
- SQLAlchemy con SQLite
- bcrypt (hash de contraseñas), PyJWT (tokens), PyOTP (códigos OTP)
- smtplib (envío de correos)
- slowapi (rate limiting) y pytest (pruebas)

## Estructura del proyecto

```
app/
├── main.py            # aplicación principal
├── models.py          # modelos SQLAlchemy (users, otp_codes, login_sessions)
├── schemas.py         # esquemas Pydantic con ejemplos
├── database.py        # configuración de la base de datos
├── middleware.py      # validación de tokens (rutas protegidas)
├── security.py        # hash de contraseñas y tokens JWT
├── limiter.py         # configuración del rate limiting
├── routes/
│   ├── auth.py        # endpoints de autenticación
│   └── users.py       # endpoints de usuario
└── services/
    ├── email_service.py   # envío de correos
    └── otp_service.py     # generación y validación de OTP
tests/                 # pruebas unitarias y de integración
```

## Instalación local

```bash
git clone <https://github.com/Praditooo/Proyecto-OTP.git>
cd proyecto_otp
python -m venv venv
venv\Scripts\activate       
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz del proyecto (no se sube a Git):

```
SECRET_KEY=una-clave-larga-y-aleatoria
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASSWORD=contraseña-de-aplicacion-de-gmail
```

Variables opcionales para usar otro servidor SMTP (por ejemplo en producción):
`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `EMAIL_FROM`.

Ejecutar el servidor:

```bash
uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000/docs` para probar la API.

## Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | /auth/register | Registrar nuevo usuario | No |
| POST | /auth/login | Validar credenciales y enviar OTP | No |
| POST | /auth/verify-otp | Verificar OTP y obtener JWT | No |
| POST | /auth/resend-otp | Reenviar código OTP | No |
| POST | /auth/refresh | Cambiar el token por uno nuevo | Sí |
| POST | /auth/logout | Cerrar sesión y revocar el token | Sí |
| GET | /users/profile | Ver perfil | Sí |
| PUT | /users/profile | Actualizar perfil | Sí |

Las rutas protegidas requieren el encabezado `Authorization: Bearer <token>`.

## Flujo de autenticación

1. `POST /auth/register` crea la cuenta (la contraseña se guarda con hash bcrypt).
2. `POST /auth/login` valida correo y contraseña y envía un OTP al correo.
3. `POST /auth/verify-otp` valida el OTP y devuelve un token JWT (expira en 30 minutos).
4. Con el token se accede a `/users/profile`. `POST /auth/logout` lo revoca.

## Seguridad

- Contraseñas con hash bcrypt (nunca se guardan en texto plano).
- OTP de 6 dígitos, válido 15 minutos y de un solo uso; al generar uno nuevo, los anteriores se invalidan.
- Tokens JWT con expiración y registro en `login_sessions`: al cerrar sesión se borra y el token queda revocado.
- Middleware que valida firma, expiración y que la sesión siga activa.
- Rate limiting por IP en register, login, resend-otp y verify-otp (respuesta 429 al excederlo).
- Mensajes de error genéricos (no revelan si un correo existe) y logs sin credenciales ni códigos.
- Secretos en variables de entorno (`.env` fuera de Git).

## Pruebas

```bash
pytest
```

Incluye 9 pruebas unitarias (hash, JWT, generación y verificación de OTP, validación de esquemas)
y 6 de integración (registro, flujo completo login → OTP → perfil, credenciales incorrectas,
rutas protegidas, logout y refresh).

## Despliegue

Desplegado en Render con las variables de entorno configuradas en el panel del servicio.

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"`

Nota: Render bloquea los puertos SMTP habituales (25, 465, 587), por lo que en producción
se usa Resend a través del puerto 2465, configurado con las variables `SMTP_*`.
En local se usa Gmail sin cambiar el código.

## Autores

_(Jack Prado)_
