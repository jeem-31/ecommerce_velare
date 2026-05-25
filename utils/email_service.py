"""Centralized email sender that works on Railway.

Railway free/hobby tier blocks outbound SMTP (ports 25/465/587). This module
prefers HTTP-based email APIs that go through ports 80/443:

    1. Resend (preferred)        - https://resend.com      3,000 free emails/month
    2. Brevo / Sendinblue        - https://brevo.com       300 free emails/day
    3. MailerSend                - https://mailersend.com  3,000 free emails/month
    4. SendGrid                  - https://sendgrid.com    100 free emails/day
    5. SMTP (Gmail) fallback     - works locally, blocked on Railway

Configure via environment variables. The first provider whose API key is set
will be used. SMTP is used only when no HTTP provider is configured.

Required env vars (one of):
    RESEND_API_KEY          re_xxxxxxxxxxxx
    BREVO_API_KEY           xkeysib-xxxxxxxxxxxx
    MAILERSEND_API_KEY      mlsn.xxxxxxxxxxxx
    SENDGRID_API_KEY        SG.xxxxxxxxxxxx

Optional:
    EMAIL_FROM              Display address for the From header
                            (default: 'Velare <onboarding@resend.dev>')
    EMAIL_REPLY_TO          Reply-To header
    SMTP_HOST, SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD           SMTP fallback (used locally)
"""

from __future__ import annotations

import os
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.environ.get(name)
    if value is None or value.strip() == '':
        return default
    return value.strip()


def _default_from() -> str:
    """Reasonable default sender used when EMAIL_FROM is unset."""
    # Resend offers a shared sandbox domain for testing without verifying a
    # custom domain. It only delivers to the account owner's email, but it
    # avoids blocking development.
    return _env('EMAIL_FROM') or 'Velare <onboarding@resend.dev>'


# ---------------------------------------------------------------------------
# HTTP providers
# ---------------------------------------------------------------------------
def _send_via_resend(to: str, subject: str, html: str, text: str) -> bool:
    api_key = _env('RESEND_API_KEY')
    if not api_key:
        return False

    payload = {
        'from': _default_from(),
        'to': [to],
        'subject': subject,
        'html': html,
        'text': text,
    }
    reply_to = _env('EMAIL_REPLY_TO')
    if reply_to:
        payload['reply_to'] = reply_to

    try:
        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        if response.status_code in (200, 202):
            print(f"✅ [Resend] Sent email to {to}")
            return True
        print(f"❌ [Resend] {response.status_code} {response.text}")
        return False
    except requests.RequestException as exc:
        print(f"❌ [Resend] Request failed: {exc}")
        return False


def _send_via_brevo(to: str, subject: str, html: str, text: str) -> bool:
    api_key = _env('BREVO_API_KEY')
    if not api_key:
        return False

    sender_value = _default_from()
    # Brevo expects sender as a structured object: {"name": ..., "email": ...}
    sender_name, sender_email = _split_address(sender_value)

    payload = {
        'sender': {'name': sender_name, 'email': sender_email},
        'to': [{'email': to}],
        'subject': subject,
        'htmlContent': html,
        'textContent': text,
    }
    reply_to = _env('EMAIL_REPLY_TO')
    if reply_to:
        rt_name, rt_email = _split_address(reply_to)
        payload['replyTo'] = {'email': rt_email, 'name': rt_name}

    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'api-key': api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        if response.status_code in (200, 201, 202):
            print(f"✅ [Brevo] Sent email to {to}")
            return True
        print(f"❌ [Brevo] {response.status_code} {response.text}")
        return False
    except requests.RequestException as exc:
        print(f"❌ [Brevo] Request failed: {exc}")
        return False


def _send_via_mailersend(to: str, subject: str, html: str, text: str) -> bool:
    api_key = _env('MAILERSEND_API_KEY')
    if not api_key:
        return False

    sender_value = _default_from()
    sender_name, sender_email = _split_address(sender_value)

    payload = {
        'from': {'email': sender_email, 'name': sender_name or 'Velare'},
        'to': [{'email': to}],
        'subject': subject,
        'html': html,
        'text': text or ' ',
    }
    reply_to = _env('EMAIL_REPLY_TO')
    if reply_to:
        rt_name, rt_email = _split_address(reply_to)
        payload['reply_to'] = {'email': rt_email, 'name': rt_name}

    try:
        response = requests.post(
            'https://api.mailersend.com/v1/email',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            json=payload,
            timeout=15,
        )
        if response.status_code in (200, 201, 202):
            print(f"✅ [MailerSend] Sent email to {to}")
            return True
        print(f"❌ [MailerSend] {response.status_code} {response.text}")
        return False
    except requests.RequestException as exc:
        print(f"❌ [MailerSend] Request failed: {exc}")
        return False


def _send_via_sendgrid(to: str, subject: str, html: str, text: str) -> bool:
    api_key = _env('SENDGRID_API_KEY')
    if not api_key:
        return False

    sender_value = _default_from()
    sender_name, sender_email = _split_address(sender_value)

    payload = {
        'personalizations': [{'to': [{'email': to}]}],
        'from': {'email': sender_email, 'name': sender_name},
        'subject': subject,
        'content': [
            {'type': 'text/plain', 'value': text or ' '},
            {'type': 'text/html', 'value': html},
        ],
    }
    reply_to = _env('EMAIL_REPLY_TO')
    if reply_to:
        rt_name, rt_email = _split_address(reply_to)
        payload['reply_to'] = {'email': rt_email, 'name': rt_name}

    try:
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        if response.status_code in (200, 201, 202):
            print(f"✅ [SendGrid] Sent email to {to}")
            return True
        print(f"❌ [SendGrid] {response.status_code} {response.text}")
        return False
    except requests.RequestException as exc:
        print(f"❌ [SendGrid] Request failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# SMTP fallback
# ---------------------------------------------------------------------------
def _send_via_smtp(to: str, subject: str, html: str, text: str) -> bool:
    host = _env('SMTP_HOST', 'smtp.gmail.com')
    port = int(_env('SMTP_PORT', '587'))
    username = _env('SMTP_USERNAME') or _env('MAIL_USERNAME')
    password = _env('SMTP_PASSWORD') or _env('MAIL_PASSWORD')

    if not username or not password:
        print("❌ [SMTP] No credentials configured")
        return False

    sender_value = _env('EMAIL_FROM') or username

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_value
    msg['To'] = to
    if text:
        msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(host, port, timeout=10)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        print(f"✅ [SMTP] Sent email to {to}")
        return True
    except smtplib.SMTPException as exc:
        print(f"❌ [SMTP] {type(exc).__name__}: {exc}")
        return False
    except OSError as exc:
        # Railway blocks outbound SMTP - this is the most common failure mode.
        print(f"❌ [SMTP] Network error (Railway blocks SMTP ports): {exc}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"❌ [SMTP] Unexpected: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def send_email(to: str, subject: str, html: str, text: str = '') -> bool:
    """Send an email using the first available provider.

    Returns True on success, False on failure. Failures are logged but never
    raise so callers can decide how to surface the error to the user.
    """
    if not to:
        print("❌ Email send skipped: no recipient")
        return False

    text_fallback = text or _strip_html(html)

    # Try HTTP providers first (work on Railway)
    for sender in (_send_via_resend, _send_via_brevo, _send_via_mailersend, _send_via_sendgrid):
        if sender(to, subject, html, text_fallback):
            return True

    # Fall back to SMTP (works locally)
    print("ℹ️ No HTTP email provider configured, trying SMTP fallback")
    return _send_via_smtp(to, subject, html, text_fallback)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _split_address(value: str):
    """Parse 'Name <email@domain>' into (name, email). Returns ('', value)
    when the value is just an email address."""
    if not value:
        return '', ''
    value = value.strip()
    if '<' in value and value.endswith('>'):
        name, _, rest = value.partition('<')
        return name.strip().strip('"'), rest[:-1].strip()
    return '', value


def _strip_html(html: str) -> str:
    """Crude HTML to text fallback - good enough for email plain-text bodies."""
    import re
    if not html:
        return ''
    text = re.sub(r'<\s*br\s*/?\s*>', '\n', html, flags=re.IGNORECASE)
    text = re.sub(r'</\s*p\s*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
