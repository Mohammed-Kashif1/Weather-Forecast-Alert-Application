"""Optional SMTP email notifications."""
import smtplib
from email.message import EmailMessage
from .config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO

class NotificationError(RuntimeError):
    pass

def email_is_configured():
    return bool(SMTP_HOST and EMAIL_FROM and EMAIL_TO)

def send_email_alerts(city, alerts):
    if not email_is_configured():
        raise NotificationError("SMTP settings are incomplete; configure SMTP_HOST, EMAIL_FROM, and EMAIL_TO in .env.")
    if not alerts:
        return False
    message = EmailMessage()
    message["Subject"] = f"Weather alerts for {city}"
    message["From"] = EMAIL_FROM
    message["To"] = EMAIL_TO
    body = [f"Weather alert summary for {city}", ""]
    for alert in alerts:
        body.extend([f"- {alert.get('type')}: {alert.get('message')}", f"  Time: {alert.get('time') or 'Current'}", ""])
    message.set_content("\n".join(body))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
    except Exception as exc:
        raise NotificationError(f"Email delivery failed: {exc}") from exc
    return True
