# app/agent/emailer.py
import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional

def send_email(to_email: str,
               subject: str,
               body: str,
               attachment_paths: Optional[List[str]] = None,
               from_email: Optional[str] = None) -> bool:
    """
    Send an email with optional multiple attachments.
    If SMTP env vars are missing, this function will simulate sending and return True.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT") or 0)
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = from_email or os.getenv("FROM_EMAIL") or smtp_user or "no-reply@example.com"

    # Simulation mode if SMTP not configured
    if not smtp_host or not smtp_user or not smtp_pass or smtp_port == 0:
        print(f"[SIMULATED EMAIL] To: {to_email} Subject: {subject} Attachments: {attachment_paths}")
        print("Body:\n", body)
        return True

    try:
        msg = EmailMessage()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        # Attach files (if provided)
        if attachment_paths:
            for path in attachment_paths:
                if not path or not os.path.exists(path):
                    continue
                with open(path, "rb") as f:
                    data = f.read()
                # Try to derive maintype/subtype from filename (pdf, ics, etc.)
                filename = os.path.basename(path)
                if filename.lower().endswith(".pdf"):
                    maintype, subtype = "application", "pdf"
                elif filename.lower().endswith(".ics"):
                    maintype, subtype = "text", "calendar"
                else:
                    maintype, subtype = "application", "octet-stream"
                msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

        # Choose SSL or STARTTLS based on port
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
        print("[EMAIL SENT] To:", to_email, "Subject:", subject)
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False
