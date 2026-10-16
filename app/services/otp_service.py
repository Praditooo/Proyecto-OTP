import hmac
from datetime import timedelta

import pyotp
from sqlalchemy.orm import Session

from app.models import OTPCode, utcnow

OTP_EXPIRE_MINUTES = 15


def create_otp(db: Session, user_id: int) -> str:
    """Genera un código OTP de 6 dígitos, válido 15 minutos, y lo guarda en la base de datos."""
    db.query(OTPCode).filter(
        OTPCode.user_id == user_id, OTPCode.used.is_(False)
    ).update({"used": True})

    code = pyotp.TOTP(pyotp.random_base32()).now()

    otp = OTPCode(
        user_id=user_id,
        code=code,
        expires_at=utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp)
    db.commit()
    return code


def verify_otp(db: Session, user_id: int, code: str) -> bool:
    """Comprueba que el código sea el último generado, no haya expirado ni se haya usado.

    Si es válido lo marca como usado, así no se puede reutilizar.
    """
    otp = (
        db.query(OTPCode)
        .filter(OTPCode.user_id == user_id, OTPCode.used.is_(False))
        .order_by(OTPCode.id.desc())
        .first()
    )
    if otp is None or otp.expires_at < utcnow():
        return False

    if not hmac.compare_digest(otp.code, code):
        return False

    otp.used = True
    db.commit()
    return True