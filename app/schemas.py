from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Datos que el cliente envía para registrarse."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "ana.perez@gmail.com",
                "password": "Clave1234",
                "full_name": "Ana Pérez",
            }
        }
    )

    @field_validator("password")
    @classmethod
    def validar_password(cls, value: str) -> str:
        """Exige letras y números, y limita el tamaño (bcrypt admite máximo 72 bytes)."""
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña es demasiado larga (máximo 72 bytes)")
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("La contraseña debe tener al menos una letra y un número")
        return value


class UserResponse(BaseModel):
    """Datos del usuario que la API devuelve (nunca incluye la contraseña)."""

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "ana.perez@gmail.com",
                "full_name": "Ana Pérez",
                "created_at": "2026-10-16T10:30:00",
            }
        },
    )

class LoginRequest(BaseModel):
    """Datos para iniciar sesión (primer paso: correo y contraseña)."""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "ana.perez@gmail.com", "password": "Clave1234"}
        }
    )


class EmailRequest(BaseModel):
    """Solicitud que solo necesita el correo (por ejemplo, reenviar el OTP)."""

    email: EmailStr

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "ana.perez@gmail.com"}}
    )


class MessageResponse(BaseModel):
    """Respuesta simple con un mensaje de texto."""

    message: str

class OTPVerifyRequest(BaseModel):
    """Datos para el segundo paso del login: correo y código OTP de 6 dígitos."""

    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "ana.perez@gmail.com", "code": "123456"}}
    )


class TokenResponse(BaseModel):
    """Token JWT que se entrega tras verificar el OTP."""

    access_token: str
    token_type: str = "bearer"