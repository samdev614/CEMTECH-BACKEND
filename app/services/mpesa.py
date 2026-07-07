import base64
import httpx
from datetime import datetime
from app.core.config import settings


def _looks_like_sandbox_config() -> bool:
    shortcode = str(settings.MPESA_SHORTCODE or "").strip()
    callback_url = str(settings.MPESA_CALLBACK_URL or "").strip().lower()
    return shortcode == "174379" or "sandbox" in callback_url


def _base_url() -> str:
    if settings.MPESA_ENV == "production" and not _looks_like_sandbox_config():
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


async def get_access_token() -> str:
    creds = base64.b64encode(
        f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    ).decode()
    async with httpx.AsyncClient() as client:
        url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"
        r = await client.get(
            url,
            headers={"Authorization": f"Basic {creds}"},
            timeout=15,
        )
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text.strip()
            hint = ""
            if settings.MPESA_ENV == "production":
                hint = (
                    "Your current credentials work on sandbox but not production. "
                    "Use MPESA_ENV=sandbox for local testing, or switch to live Daraja "
                    "credentials, a live shortcode/paybill, and a production callback URL."
                )
            raise RuntimeError(
                f"Daraja OAuth failed with {exc.response.status_code} from {_base_url()}. "
                f"{body or 'No response body returned.'} {hint}".strip()
            ) from exc
        return r.json()["access_token"]


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _password(timestamp: str) -> str:
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


async def stk_push(phone: str, amount: int, order_id: int, description: str) -> dict:
    """Initiate Lipa Na M-Pesa STK Push. Returns Daraja response dict."""
    token = await get_access_token()
    ts = _timestamp()
    # Normalise phone: 07xx → 2547xx
    phone = phone.strip().replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": _password(ts),
        "Timestamp": ts,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"ORDER-{order_id}",
        "TransactionDesc": description[:13],
    }
    async with httpx.AsyncClient() as client:
        url = f"{_base_url()}/mpesa/stkpush/v1/processrequest"
        r = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text.strip()
            raise RuntimeError(
                f"Daraja STK push failed with {exc.response.status_code} from {_base_url()}. "
                f"{body or 'No response body returned.'}"
            ) from exc
        return r.json()
