#!/usr/bin/env python
# -----------------------------------------------------------------------------
"""
Email service
=============
Async email sending via aiosmtplib.

Usage::

    from app.services.email import send_email

    await send_email(
        to="user@example.com",
        subject="Password Reset",
        body_text="Click here: ...",
        body_html="<p>Click here: ...</p>",
    )

If SMTP is not configured (smtp_host is empty) the email is logged at WARNING
level and silently dropped — so the app works without an SMTP server in dev.
"""
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------

async def send_email(
    to: str | list[str],
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    cc: Optional[list[str]] = None,
    reply_to: Optional[str] = None,
) -> bool:
    """
    Send an email.  Returns True on success, False on failure.
    Never raises — callers should not crash because of a mail error.
    """
    from app.core.config import get_settings
    settings = get_settings()

    if not settings.smtp_enabled:
        logger.warning(
            "SMTP not configured — dropping email to %s: %s", to, subject
        )
        return False

    recipients = [to] if isinstance(to, str) else to

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{settings.effective_from_name} <{settings.effective_from_address}>"
    msg["To"]      = ", ".join(recipients)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if reply_to:
        msg["Reply-To"] = reply_to

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        import aiosmtplib
    except ImportError:
        logger.error("aiosmtplib not installed — cannot send email. Run: pip install aiosmtplib")
        return False

    try:
        all_recipients = recipients + (cc or [])
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username or None,
            password=settings.smtp_password or None,
            use_tls=settings.smtp_use_ssl,
            start_tls=settings.smtp_use_tls,
        )
        logger.info("Email sent to %s: %s", recipients, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", recipients, exc)
        return False


# -----------------------------------------------------------------------------

async def send_password_reset_email(
    to: str,
    username: str,
    reset_url: str,
    site_name: str,
) -> bool:
    subject = f"[{site_name}] Password Reset Request"

    body_text = f"""\
Hi {username},

Someone requested a password reset for your {site_name} account.

Click the link below to set a new password (valid for 1 hour):

  {reset_url}

If you did not request this, you can safely ignore this email.
Your password will not change unless you click the link above.

— {site_name}
"""

    body_html = f"""\
<!DOCTYPE html>
<html>
<body style="font-family:sans-serif; max-width:520px; margin:2rem auto; color:#333;">
  <h2 style="color:#2563eb;">Password Reset — {site_name}</h2>
  <p>Hi <strong>{username}</strong>,</p>
  <p>Someone requested a password reset for your <strong>{site_name}</strong> account.</p>
  <p style="margin:1.5rem 0;">
    <a href="{reset_url}"
       style="background:#2563eb; color:#fff; padding:.6rem 1.2rem;
              border-radius:4px; text-decoration:none; font-weight:600;">
      Reset My Password
    </a>
  </p>
  <p style="color:#666; font-size:.9rem;">
    This link expires in <strong>1 hour</strong>.
    If you did not request this, you can safely ignore this email.
  </p>
  <hr style="border:none; border-top:1px solid #e5e7eb; margin:1.5rem 0;">
  <p style="color:#999; font-size:.8rem;">— {site_name}</p>
</body>
</html>
"""
    return await send_email(to=to, subject=subject, body_text=body_text, body_html=body_html)
