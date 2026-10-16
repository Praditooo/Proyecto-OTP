from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.middleware import get_current_session
from fastapi import Request
from app.limiter import limiter

from app.database import get_db
from app.models import LoginSession, User
from app.schemas import (
    EmailRequest,
    LoginRequest,
    MessageResponse,
    OTPVerifyRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.security import create_access_token, hash_password, verify_password
from app.services.email_service import send_otp_email
from app.services.otp_service import create_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, data: UserCreate, db: Session = Depends(get_db)):
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
@limiter.limit("5/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
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
@limiter.limit("3/minute")
def resend_otp(request: Request, data: EmailRequest, db: Session = Depends(get_db)):
    """Reenvía un nuevo OTP. Responde igual exista o no el correo, para no revelar usuarios."""
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user:
        code = create_otp(db, user.id)
        send_otp_email(user.email, code)
    return {"message": "Si el correo está registrado, te enviamos un nuevo código"}


@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit("5/minute")
def verify_otp_code(request: Request, data: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Segundo paso del login: verifica el OTP y entrega un token JWT con expiración.

    El token también se guarda en login_sessions para poder revocarlo al cerrar sesión.
    """
    user = db.query(User).filter(User.email == data.email.lower()).first()

    if not user or not verify_otp(db, user.id, data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código inválido o expirado",
        )

    token, expires_at = create_access_token(user.id)
    db.add(LoginSession(user_id=user.id, token=token, expires_at=expires_at))
    db.commit()
    return {"access_token": token, "token_type": "bearer"}

@router.post("/refresh", response_model=TokenResponse)
def refresh(
    session: LoginSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """Cambia el token actual por uno nuevo. El anterior queda revocado."""
    user_id = session.user_id
    new_token, expires_at = create_access_token(user_id)

    db.delete(session)  # el token viejo deja de servir
    db.add(LoginSession(user_id=user_id, token=new_token, expires_at=expires_at))
    db.commit()
    return {"access_token": new_token, "token_type": "bearer"}


@router.post("/logout", response_model=MessageResponse)
def logout(
    session: LoginSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """Cierra la sesión: borra el token de login_sessions, por lo que queda revocado."""
    db.delete(session)
    db.commit()
    return {"message": "Sesión cerrada correctamente"}