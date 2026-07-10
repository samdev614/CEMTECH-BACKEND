import base64
import httpx
from datetime import datetime
from app.core.config import settings


class DarajaError(RuntimeError):
    def __init__(self, operation: str, base_url: str, status_code: int | None = None, body: str = "", hint: str = ""):
        self.operation = operation
        self.base_url = base_url
        self.status_code = status_code
        self.body = body
        self.hint = hint

        status_text = status_code if status_code is not None else "unknown"
        message = f"Daraja {operation} failed with {status_text} from {base_url}."
        if body:
            message = f"{message} {body}"
        if hint:
            message = f"{message} {hint}"

        super().__init__(message.strip())


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
    base_url = _base_url()
    try:
        async with httpx.AsyncClient() as client:
            url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
            r = await client.get(
                url,
                headers={"Authorization": f"Basic {creds}"},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()["access_token"]
    except httpx.HTTPStatusError as exc:
        body = exc.response.text.strip()
        hint = ""
        if settings.MPESA_ENV == "production":
            hint = (
                "Your current credentials work on sandbox but not production. "
                "Use MPESA_ENV=sandbox for local testing, or switch to live Daraja "
                "credentials, a live shortcode/paybill, and a production callback URL."
            )
        raise DarajaError("OAuth", base_url, exc.response.status_code, body or "No response body returned.", hint) from exc
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise DarajaError("OAuth", base_url, None, str(exc) or "No response body returned.") from exc


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
    base_url = _base_url()
    try:
        async with httpx.AsyncClient() as client:
            url = f"{base_url}/mpesa/stkpush/v1/processrequest"
            r = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text.strip()
        raise DarajaError("STK push", base_url, exc.response.status_code, body or "No response body returned.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise DarajaError("STK push", base_url, None, str(exc) or "No response body returned.") from exc


async def stk_query(checkout_request_id: str) -> dict:
    """Query the current STK push status for a checkout request."""
    token = await get_access_token()
    ts = _timestamp()
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": _password(ts),
        "Timestamp": ts,
        "CheckoutRequestID": checkout_request_id,
    }

    base_url = _base_url()
    try:
        async with httpx.AsyncClient() as client:
            url = f"{base_url}/mpesa/stkpushquery/v1/query"
            r = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text.strip()
        raise DarajaError("STK query", base_url, exc.response.status_code, body or "No response body returned.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise DarajaError("STK query", base_url, None, str(exc) or "No response body returned.") from exc
