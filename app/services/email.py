import resend
from app.core.config import settings


def _client():
    resend.api_key = settings.RESEND_API_KEY


# ── Contact form ──────────────────────────────────────────────────────

def send_contact_notification(name: str, email: str, subject: str, message: str):
    """Alert admin about a new contact form submission."""
    if not settings.RESEND_API_KEY or not settings.ADMIN_EMAIL_NOTIFY:
        return
    _client()
    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [settings.ADMIN_EMAIL_NOTIFY],
        "subject": f"New message: {subject or 'No subject'} — {name}",
        "html": f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
          <div style="background:#D4A020;padding:20px 32px;border-radius:8px 8px 0 0">
            <h2 style="color:#fff;margin:0;font-size:20px">New Contact Message</h2>
          </div>
          <div style="background:#f9f9f9;padding:28px 32px;border-radius:0 0 8px 8px;border:1px solid #e0e0e0;border-top:none">
            <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
              <tr><td style="padding:8px 0;color:#666;width:100px">Name</td><td style="padding:8px 0;font-weight:600">{name}</td></tr>
              <tr><td style="padding:8px 0;color:#666">Email</td><td style="padding:8px 0"><a href="mailto:{email}">{email}</a></td></tr>
              <tr><td style="padding:8px 0;color:#666">Subject</td><td style="padding:8px 0">{subject or '—'}</td></tr>
            </table>
            <div style="background:#fff;border:1px solid #e0e0e0;border-radius:6px;padding:16px 20px;white-space:pre-wrap;font-size:15px;line-height:1.6">{message}</div>
            <div style="margin-top:20px">
              <a href="mailto:{email}?subject=Re: {subject or 'Your message'}" style="background:#D4A020;color:#fff;padding:10px 22px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px">Reply to {name}</a>
            </div>
          </div>
        </div>
        """,
    })


def send_contact_autoreply(name: str, email: str, subject: str):
    """Auto-reply to the person who submitted the contact form."""
    if not settings.RESEND_API_KEY:
        return
    _client()
    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [email],
        "subject": "Thanks for reaching out — I'll be in touch soon",
        "html": f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
          <div style="background:#D4A020;padding:20px 32px;border-radius:8px 8px 0 0">
            <h2 style="color:#fff;margin:0;font-size:20px">Message Received ✓</h2>
          </div>
          <div style="background:#f9f9f9;padding:28px 32px;border-radius:0 0 8px 8px;border:1px solid #e0e0e0;border-top:none">
            <p style="font-size:16px;margin:0 0 16px">Hi <strong>{name}</strong>,</p>
            <p style="color:#444;line-height:1.7;margin:0 0 16px">
              Thanks for getting in touch. I've received your message about
              <strong>"{subject or 'your enquiry'}"</strong> and will get back to you within 24 hours.
            </p>
            <p style="color:#444;line-height:1.7;margin:0 0 24px">
              In the meantime, feel free to browse my
              <a href="https://cemtech.dev/portfolio" style="color:#D4A020">portfolio</a> or
              <a href="https://cemtech.dev/shop" style="color:#D4A020">digital products</a>.
            </p>
            <p style="color:#888;font-size:13px;margin:0">— CEMTECH</p>
          </div>
        </div>
        """,
    })


# ── M-Pesa payment ────────────────────────────────────────────────────

def send_payment_confirmation(
    customer_name: str,
    customer_email: str,
    product_name: str,
    mpesa_receipt: str,
    download_url: str,
):
    """Send download link + receipt to customer after successful payment."""
    if not settings.RESEND_API_KEY:
        return
    _client()
    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [customer_email],
        "subject": f"Your download is ready — {product_name}",
        "html": f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
          <div style="background:#D4A020;padding:20px 32px;border-radius:8px 8px 0 0">
            <h2 style="color:#fff;margin:0;font-size:20px">Payment Confirmed ✓</h2>
          </div>
          <div style="background:#f9f9f9;padding:28px 32px;border-radius:0 0 8px 8px;border:1px solid #e0e0e0;border-top:none">
            <p style="font-size:16px;margin:0 0 16px">Hi <strong>{customer_name}</strong>,</p>
            <p style="color:#444;line-height:1.7;margin:0 0 20px">
              Your payment for <strong>{product_name}</strong> was successful.
              Your M-Pesa receipt number is <strong>{mpesa_receipt}</strong>.
            </p>
            <div style="text-align:center;margin:28px 0">
              <a href="{download_url}"
                 style="background:#D4A020;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;display:inline-block">
                ⬇ Download {product_name}
              </a>
            </div>
            <div style="background:#fff3cd;border:1px solid #ffe08a;border-radius:6px;padding:12px 16px;font-size:13px;color:#856404">
              ⚠ This download link is <strong>one-time use only</strong>. Save your file immediately after downloading.
            </div>
            <p style="color:#888;font-size:13px;margin:24px 0 0">— CEMTECH</p>
          </div>
        </div>
        """,
    })
