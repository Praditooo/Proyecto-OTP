"""Configuración compartida de las pruebas (fixtures de pytest)."""
import os

# Debe ir ANTES de importar la app: security.py exige SECRET_KEY al cargarse.
os.environ.setdefault("SECRET_KEY", "clave-secreta-solo-para-tests-1234567890")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.limiter import limiter
from app.main import app


@pytest.fixture()
def engine():
    """Base de datos SQLite en memoria, nueva y vacía para cada prueba."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # mantiene la misma conexión en memoria
    )
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture()
def db(engine):
    """Sesión de base de datos para las pruebas unitarias."""
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    yield session
    session.close()


@pytest.fixture()
def sent_emails():
    """Lista donde se guardan los correos 'enviados' (no se manda ninguno de verdad)."""
    return []


@pytest.fixture()
def client(engine, sent_emails, monkeypatch):
    """Cliente HTTP de pruebas conectado a la base en memoria y sin enviar correos."""
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    def fake_send_otp_email(to_email, code):
        sent_emails.append({"to": to_email, "code": code})
        return True

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.routes.auth.send_otp_email", fake_send_otp_email)
    limiter.enabled = False  # si no, el rate limit bloquearía las pruebas

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    limiter.enabled = True
