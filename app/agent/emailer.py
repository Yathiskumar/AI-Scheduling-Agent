# app/agent/emailer.py
import os
import smtplib
from email.message import EmailMessage

def send_email(to_email: str, subject: str, body: str, attachment_path: str = None) -> bool:
    """
    Send email with optional attachment if SMTP is configured via .env.
    If SMTP vars are missing, this function will simulate send and return True.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT") or 0)
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = os.getenv("FROM_EMAIL", smtp_user or "no-reply@example.com")

    # Simulation mode if SMTP not configured
    if not smtp_host or not smtp_user or not smtp_pass:
        print(f"[SIMULATED EMAIL] To: {to_email} Subject: {subject} Attachment: {attachment_path}")
        return True

    try:
        msg = EmailMessage()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                data = f.read()
            maintype = "application"
            subtype = "pdf"
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=os.path.basename(attachment_path))

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False
