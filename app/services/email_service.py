import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_otp_email(to_email: str, code: str) -> bool:
    """Envía el código OTP por correo con smtplib. Devuelve True si se envió bien."""
    msg = EmailMessage()
    msg["Subject"] = "Tu código de verificación"
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg.set_content(
        f"Tu código de verificación es: {code}\n\n"
        "Es válido por 15 minutos. Si no fuiste tú, ignora este mensaje."
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as exc:
        logger.error("Fallo al enviar el correo OTP (%s)", type(exc).__name__)
        return False