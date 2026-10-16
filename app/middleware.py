from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LoginSession, User, utcnow
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "No autenticado") -> HTTPException:
    """Construye la respuesta 401 estándar para token ausente o inválido."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> LoginSession:
    """Valida el token de la petición y devuelve su sesión activa.

    Falla con 401 si no hay token, si la firma o expiración no son válidas,
    o si la sesión fue cerrada (token revocado).
    """
    if credentials is None:
        raise _unauthorized()

    token = credentials.credentials
    if decode_access_token(token) is None:
        raise _unauthorized("Token inválido o expirado")

    session = db.query(LoginSession).filter(LoginSession.token == token).first()
    if session is None or session.expires_at < utcnow():
        raise _unauthorized("Sesión cerrada o expirada")
    return session


def get_current_user(
    session: LoginSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> User:
    """Devuelve el usuario dueño del token. Se usa en las rutas protegidas."""
    user = db.query(User).filter(User.id == session.user_id).first()
    if user is None:
        raise _unauthorized()
    return user