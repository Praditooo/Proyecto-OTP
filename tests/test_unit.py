"""Pruebas unitarias: prueban funciones sueltas, sin pasar por la API."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pydantic import ValidationError

from app.models import OTPCode, User, utcnow
from app.schemas import UserCreate
from app.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.otp_service import create_otp, verify_otp


def crear_usuario(db):
    """Crea un usuario de prueba en la base de datos en memoria."""
    user = User(
        email="ana.perez@gmail.com",
        password_hash=hash_password("Clave1234"),
        full_name="Ana Pérez",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_hash_no_guarda_texto_plano_y_se_puede_verificar():
    hashed = hash_password("Clave1234")
    assert hashed != "Clave1234"
    assert verify_password("Clave1234", hashed) is True
    assert verify_password("OtraClave99", hashed) is False


def test_token_jwt_contiene_usuario_y_expiracion():
    token, expires_at = create_access_token(7)
    payload = decode_access_token(token)
    assert payload["sub"] == "7"
    assert "exp" in payload
    assert expires_at > utcnow()


def test_token_invalido_o_firmado_con_otra_clave_se_rechaza():
    assert decode_access_token("esto-no-es-un-token") is None
    falso = jwt.encode(
        {"sub": "1"}, "otra-clave-distinta-de-32-caracteres-o-mas", algorithm=ALGORITHM
    )
    assert decode_access_token(falso) is None


def test_token_expirado_se_rechaza():
    ayer = datetime.now(timezone.utc) - timedelta(minutes=1)
    expirado = jwt.encode({"sub": "1", "exp": ayer}, SECRET_KEY, algorithm=ALGORITHM)
    assert decode_access_token(expirado) is None


def test_create_otp_genera_6_digitos_validos_15_minutos(db):
    user = crear_usuario(db)
    code = create_otp(db, user.id)

    assert len(code) == 6 and code.isdigit()
    otp = db.query(OTPCode).filter(OTPCode.user_id == user.id).first()
    assert otp.code == code
    assert otp.used is False
    restante = otp.expires_at - utcnow()
    assert timedelta(minutes=14) < restante <= timedelta(minutes=15)


def test_verify_otp_acepta_el_codigo_correcto_una_sola_vez(db):
    user = crear_usuario(db)
    code = create_otp(db, user.id)

    assert verify_otp(db, user.id, code) is True
    assert verify_otp(db, user.id, code) is False  # ya fue usado


def test_verify_otp_rechaza_codigo_incorrecto(db):
    user = crear_usuario(db)
    code = create_otp(db, user.id)
    incorrecto = "000000" if code != "000000" else "111111"

    assert verify_otp(db, user.id, incorrecto) is False


def test_verify_otp_rechaza_codigo_expirado(db):
    user = crear_usuario(db)
    code = create_otp(db, user.id)
    otp = db.query(OTPCode).filter(OTPCode.user_id == user.id).first()
    otp.expires_at = utcnow() - timedelta(minutes=1)
    db.commit()

    assert verify_otp(db, user.id, code) is False


def test_schema_rechaza_contrasena_sin_numeros():
    with pytest.raises(ValidationError):
        UserCreate(
            email="ana.perez@gmail.com", password="soloLetrasAqui", full_name="Ana Pérez"
        )
