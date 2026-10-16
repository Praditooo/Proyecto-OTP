from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    EmailRequest,
    LoginRequest,
    MessageResponse,
    UserCreate,
    UserResponse,
)
from app.security import hash_password, verify_password
from app.services.email_service import send_otp_email
from app.services.otp_service import create_otp

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario.

    Valida el email, comprueba que no exista y guarda la contraseña como hash bcrypt.
    """
    email = data.email.lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )

    user = User(
        email=email,
        password_hash=hash_password(data.password),  # se guarda el hash, no la contraseña
        full_name=data.full_name,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )
    db.refresh(user)
    return user


@router.post("/login", response_model=MessageResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Primer paso del login: valida correo y contraseña y envía un OTP por correo."""
    user = db.query(User).filter(User.email == data.email.lower()).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    code = create_otp(db, user.id)
    if not send_otp_email(user.email, code):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo enviar el código. Intenta de nuevo",
        )
    return {"message": "Te enviamos un código de verificación a tu correo"}


@router.post("/resend-otp", response_model=MessageResponse)
def resend_otp(data: EmailRequest, db: Session = Depends(get_db)):
    """Reenvía un nuevo OTP. Responde igual exista o no el correo, para no revelar usuarios."""
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user:
        code = create_otp(db, user.id)
        send_otp_email(user.email, code)
    return {"message": "Si el correo está registrado, te enviamos un nuevo código"}