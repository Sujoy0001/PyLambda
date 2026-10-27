import smtplib
from email.message import EmailMessage

from app.core.config import settings


def validate_smtp_configuration() -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        raise RuntimeError(
            "SMTP_HOST and SMTP_FROM_EMAIL must be configured"
        )
    if settings.SMTP_USERNAME and not settings.SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_PASSWORD must be configured when SMTP_USERNAME is set"
        )


def send_password_reset_email(recipient: str, token: str) -> None:
    validate_smtp_configuration()

    message = EmailMessage()
    message["Subject"] = "Reset your PyLambda password"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient
    message.set_content(
        "A password reset was requested for your PyLambda account.\n\n"
        f"Use this one-time token within "
        f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes:\n\n"
        f"{token}\n\n"
        "Send a POST request with this token and your new password to:\n"
        f"{settings.PASSWORD_RESET_API_URL}\n"
        'JSON body: {"token": "<token>", '
        '"new_password": "<your-new-password>"}\n\n'
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(
        settings.SMTP_HOST, settings.SMTP_PORT, timeout=10
    ) as server:
        server.ehlo()
        if settings.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)
