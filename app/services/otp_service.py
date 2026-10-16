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