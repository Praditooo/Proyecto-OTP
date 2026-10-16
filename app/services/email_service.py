import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_USER = os.getenv("EMAIL_USER")
SMTP_USER = os.getenv("SMTP_USER", EMAIL_USER)  # usuario para iniciar sesión en el SMTP
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)  # dirección que aparece como remitente


def send_otp_email(to_email: str, code: str) -> bool:
    """Envía el código OTP por correo con smtplib. Devuelve True si se envió bien."""
    msg = EmailMessage()
    msg["Subject"] = "Tu código de verificación"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg.set_content(
        f"Tu código de verificación es: {code}\n\n"
        "Es válido por 15 minutos. Si no fuiste tú, ignora este mensaje."
    )

    use_ssl = SMTP_PORT in (465, 2465)
    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP

    try:
        with smtp_class(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if not use_ssl:
                server.starttls()
            server.login(SMTP_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as exc:
        logger.error("Fallo al enviar el correo OTP (%s)", type(exc).__name__)
        return False