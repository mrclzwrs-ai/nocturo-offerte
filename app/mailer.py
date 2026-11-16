"""Offertes mailen via SMTP (bijv. info@nocturoapps.com in Google Workspace).

Instellen met omgevingsvariabelen: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM.
De mail gaat uit namens het bedrijf ("Bedrijf via Nocturo"); antwoorden gaan naar het bedrijf zelf.
"""
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr


def mail_ready() -> bool:
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASSWORD"))


def send_quote_mail(company, to: str, subject: str, body: str, pdf_bytes: bytes, filename: str):
    sender = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER")
    msg = EmailMessage()
    msg["From"] = formataddr((f"{company.name} via Nocturo", sender))
    msg["To"] = to
    msg["Reply-To"] = company.email
    msg["Subject"] = subject
    msg.set_content(body)
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        s.send_message(msg, to_addrs=[to, company.email])  # bedrijf krijgt een kopie
