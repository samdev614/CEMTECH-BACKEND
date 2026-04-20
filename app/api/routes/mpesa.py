import secrets
import mimetypes
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from app.models.product import Product, Order
from app.schemas.product import OrderOut
from app.services.mpesa import stk_push
from app.services.email import send_payment_confirmation
from app.core.config import settings

# Mounted under /api/products
buy_router = APIRouter()

# Mounted under /api  (avoids slug collision with /{slug})
util_router = APIRouter()


class BuyRequest(BaseModel):
    name: str
    email: str
    phone: str


@buy_router.post("/{slug}/buy", response_model=OrderOut)
async def buy_product(slug: str, body: BuyRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug, Product.is_published == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    order = Order(
        product_id=product.id,
        customer_name=body.name,
        customer_email=body.email,
        customer_phone=body.phone,
        amount=product.price,
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    try:
        resp = await stk_push(
            phone=body.phone,
            amount=int(product.price),
            order_id=order.id,
            description=product.name,
        )
        order.mpesa_ref = resp.get("CheckoutRequestID", "")
        db.commit()
    except Exception as e:
        order.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"M-Pesa push failed: {str(e)}")

    return order


@util_router.get("/order/{order_id}/status")
def order_status(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": order.id,
        "status": order.status,
        "download_token": order.download_token if order.status == "paid" else None,
        "mpesa_receipt": order.mpesa_ref if order.status == "paid" else None,
    }


@util_router.post("/mpesa/callback")
async def mpesa_callback(payload: dict, db: Session = Depends(get_db)):
    """Safaricom Daraja STK Push callback."""
    try:
        stk = payload["Body"]["stkCallback"]
        result_code = stk["ResultCode"]
        checkout_id = stk["CheckoutRequestID"]

        order = db.query(Order).filter(Order.mpesa_ref == checkout_id).first()
        if not order:
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        if result_code == 0:
            items = {i["Name"]: i.get("Value") for i in stk["CallbackMetadata"]["Item"]}
            order.status = "paid"
            order.mpesa_ref = str(items.get("MpesaReceiptNumber", checkout_id))
            order.download_token = secrets.token_urlsafe(32)
            product = db.query(Product).filter(Product.id == order.product_id).first()
            if product:
                product.sales_count = (product.sales_count or 0) + 1
            db.commit()
            base_url = settings.MPESA_CALLBACK_URL.split('/api/')[0]
            download_url = f"{base_url}/api/download/{order.download_token}"
            try:
                send_payment_confirmation(
                    order.customer_name, order.customer_email,
                    product.name if product else "Your purchase",
                    order.mpesa_ref, download_url,
                )
            except Exception:
                pass
        else:
            order.status = "failed"
            db.commit()
    except Exception:
        pass

    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@util_router.get("/download/{token}")
def download_file(token: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        Order.download_token == token,
        Order.status == "paid",
        Order.download_used == False,
    ).first()
    if not order:
        raise HTTPException(status_code=403, detail="Invalid or already used download link")

    product = db.query(Product).filter(Product.id == order.product_id).first()
    if not product or not product.file_path:
        raise HTTPException(status_code=404, detail="File not found")

    # file_path is stored as a URL path like /uploads/products/file.zip
    # strip the leading slash so Path resolves relative to the backend working directory
    file_path = Path(product.file_path.lstrip('/'))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    order.download_used = True
    db.commit()

    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        path=str(file_path),
        filename=product.name.replace(' ', '_') + file_path.suffix,
        media_type=media_type or "application/octet-stream",
    )
