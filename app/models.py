from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.database import Base


def utcnow():
    """Fecha y hora actual en UTC (sin zona horaria, para que SQLite las compare bien)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

    
class User(Base):
    """Usuarios registrados en el sistema."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)  # nunca se guarda la contraseña real
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class OTPCode(Base):
    """Códigos OTP generados para cada usuario, con su expiración."""
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)  # un código solo se puede usar una vez
    created_at = Column(DateTime, default=utcnow)


class LoginSession(Base):
    """Sesiones activas: guarda los tokens JWT vigentes (si se borra, el token queda revocado)."""
    __tablename__ = "login_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utcnow)