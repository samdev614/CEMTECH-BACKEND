import secrets
import mimetypes
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status # Import status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from app.models.product import Product, Order
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.schemas.product import OrderOut
from app.core.security import get_current_user
from app.services.mpesa import DarajaError, stk_push, stk_query
from app.services.email import send_payment_confirmation
from app.core.config import settings

logger = logging.getLogger(__name__)

# Mounted under /api/products
product_buy_router = APIRouter()

# Mounted under /api/courses
course_buy_router = APIRouter()

# Mounted under /api
util_router = APIRouter()


class BuyRequest(BaseModel):
    name: str
    email: str
    phone: str


def _callback_items(stk_callback: dict) -> dict:
    metadata = stk_callback.get("CallbackMetadata") or {}
    items = metadata.get("Item") or []
    parsed = {}

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("Name")
            if name:
                parsed[name] = item.get("Value")

    return parsed


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _mpesa_reconciliation_due(order: Order) -> bool:
    cooldown_seconds = max(int(getattr(settings, "MPESA_STATUS_QUERY_COOLDOWN_SECONDS", 60)), 0)
    last_checked_at = _aware_datetime(order.mpesa_last_query_at)
    if last_checked_at is None:
        return True
    return (_utcnow() - last_checked_at).total_seconds() >= cooldown_seconds


def _mark_mpesa_reconciliation_attempt(order: Order, db: Session) -> None:
    order.mpesa_last_query_at = _utcnow()
    db.commit()
    db.refresh(order)


def _order_item_details(order: Order, db: Session) -> tuple[str, str | None]:
    item_name = "Your purchase"
    download_url = None

    if order.item_type == "product" and order.product_id:
        product = db.query(Product).filter(Product.id == order.product_id).first()
        if product:
            item_name = product.name
        if order.download_token:
            base_url = settings.MPESA_CALLBACK_URL.split('/api/')[0]
            download_url = f"{base_url}/api/download/{order.download_token}"
    elif order.item_type == "course" and order.course_id:
        course = db.query(Course).filter(Course.id == order.course_id).first()
        if course:
            item_name = course.title

    return item_name, download_url


def _finalize_paid_order(order: Order, db: Session, receipt_number: str | None = None) -> tuple[str, str | None, bool]:
    transitioned = order.status != "paid"

    if transitioned:
        order.status = "paid"
        if receipt_number:
            order.mpesa_ref = str(receipt_number)

        if order.item_type == "product":
            order.download_token = order.download_token or secrets.token_urlsafe(32)

        if order.item_type == "product" and order.product_id:
            product = db.query(Product).filter(Product.id == order.product_id).first()
            if product:
                product.sales_count = (product.sales_count or 0) + 1
        elif order.item_type == "course" and order.course_id:
            enrollment = db.query(Enrollment).filter(
                Enrollment.user_id == order.user_id,
                Enrollment.course_id == order.course_id,
            ).first()

            if not enrollment:
                enrollment = Enrollment(
                    user_id=order.user_id,
                    course_id=order.course_id,
                    price_paid=order.amount,
                    status="active",
                    payment_status="paid",
                )
                db.add(enrollment)
            else:
                enrollment.status = "active"
                enrollment.payment_status = "paid"

        db.commit()
        db.refresh(order)
    elif receipt_number and order.mpesa_ref != str(receipt_number):
        order.mpesa_ref = str(receipt_number)
        db.commit()
        db.refresh(order)

    return (*_order_item_details(order, db), transitioned)


@product_buy_router.post("/{slug}/buy", response_model=OrderOut)
async def buy_product(slug: str, body: BuyRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    product = db.query(Product).filter(Product.slug == slug, Product.is_published == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    order = Order(
        product_id=product.id,
        user_id=current_user.id if current_user else None,
        item_type="product",
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
        # Ensure amount is an integer for M-Pesa
        mpesa_amount = int(product.price)
        if mpesa_amount <= 0:
            raise HTTPException(status_code=400, detail="Product price must be greater than zero for M-Pesa payment.")

        resp = await stk_push(
            phone=body.phone,
            amount=mpesa_amount,
            order_id=order.id,
            description=product.name,
        )
        order.mpesa_ref = resp.get("CheckoutRequestID", "")
        db.commit()
    except Exception as e:
        order.status = "failed"
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"M-Pesa push failed: {str(e)}") # Changed to 502

    return order


@course_buy_router.post("/{slug}/buy", response_model=OrderOut)
async def buy_course(slug: str, body: BuyRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    course = db.query(Course).filter(Course.slug == slug, Course.is_published == True).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing_order = (
        db.query(Order)
        .filter(
            Order.course_id == course.id,
            Order.item_type == "course",
            or_(Order.user_id == current_user.id, Order.customer_email == current_user.email),
            Order.status.in_(["pending", "paid"]),
        )
        .order_by(Order.created_at.desc())
        .first()
    )
    if existing_order:
        if existing_order.status == "paid":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already own this course.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A payment for this course is already in progress.")

    buyer_name = (body.name.strip() or current_user.full_name or current_user.email).strip()
    buyer_email = current_user.email

    # Create an order for the course
    order = Order(
        course_id=course.id, # Link to course
        user_id=current_user.id,
        item_type="course", # Specify item type
        customer_name=buyer_name,
        customer_email=buyer_email,
        customer_phone=body.phone,
        amount=course.price,
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    try:
        mpesa_amount = int(course.price)
        if mpesa_amount <= 0:
            raise HTTPException(status_code=400, detail="Course price must be greater than zero for M-Pesa payment.")

        resp = await stk_push(
            phone=body.phone,
            amount=mpesa_amount,
            order_id=order.id,
            description=course.title,
        )
        order.mpesa_ref = resp.get("CheckoutRequestID", "")
        db.commit()
    except Exception as e:
        order.status = "failed"
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"M-Pesa push failed: {str(e)}") # Changed to 502

    return order


@util_router.get("/order/{order_id}/status")
async def order_status(order_id: int, force_reconcile: bool = Query(False), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "pending" and order.mpesa_ref and (force_reconcile or _mpesa_reconciliation_due(order)):
        try:
            _mark_mpesa_reconciliation_attempt(order, db)
            query_response = await stk_query(order.mpesa_ref)
            logger.info(
                "M-Pesa status query for order %s: %s",
                order.id,
                query_response,
            )
            result_code_raw = query_response.get("ResultCode")
            try:
                result_code = int(result_code_raw)
            except (TypeError, ValueError):
                result_code = None

            if result_code == 0:
                item_name, download_url, transitioned = _finalize_paid_order(order, db)
                if transitioned:
                    try:
                        send_payment_confirmation(
                            order.customer_name,
                            order.customer_email,
                            item_name,
                            order.mpesa_ref,
                            download_url,
                            item_type=order.item_type,
                        )
                        logger.info("M-Pesa status query - confirmation email sent for order %s.", order.id)
                    except Exception:
                        logger.exception("Failed to send payment confirmation email after status reconciliation")
            elif result_code in {1032, 1037}:
                order.status = "failed"
                db.commit()
                db.refresh(order)
        except DarajaError as exc:
            if exc.status_code in {403, 429}:
                logger.warning(
                    "M-Pesa status reconciliation paused for order %s after Daraja %s: %s",
                    order.id,
                    exc.status_code,
                    exc,
                )
            else:
                logger.warning("M-Pesa status reconciliation failed for order %s: %s", order.id, exc)
        except Exception:
            logger.exception("M-Pesa status reconciliation failed for order %s", order.id)

    db.refresh(order)
    return {
        "id": order.id,
        "status": order.status,
        "download_token": order.download_token if order.status == "paid" and order.item_type == "product" else None,
        "mpesa_receipt": order.mpesa_ref if order.status == "paid" else None,
    }


@util_router.post("/mpesa/callback")
async def mpesa_callback(payload: dict, db: Session = Depends(get_db)):
    """Safaricom Daraja STK Push callback."""
    logger.info(f"M-Pesa callback received: {payload}")

    try:
        stk = payload["Body"]["stkCallback"]
        result_code = stk.get("ResultCode")
        checkout_id = stk.get("CheckoutRequestID")

        logger.info(f"M-Pesa callback - CheckoutRequestID: {checkout_id}, ResultCode: {result_code}")

        order = db.query(Order).filter(Order.mpesa_ref == checkout_id).first()
        if not order:
            logger.warning(f"M-Pesa callback - Order not found for CheckoutRequestID: {checkout_id}")
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        try:
            result_code_value = int(result_code)
        except (TypeError, ValueError):
            result_code_value = None

        if result_code_value == 0:
            items = _callback_items(stk)
            mpesa_receipt_number = items.get("MpesaReceiptNumber") or checkout_id
            logger.info(f"M-Pesa callback - Payment successful for order {order.id}. Receipt: {mpesa_receipt_number}")

            item_name, download_url, transitioned = _finalize_paid_order(order, db, mpesa_receipt_number)
            if transitioned:
                try:
                    send_payment_confirmation(
                        order.customer_name,
                        order.customer_email,
                        item_name,
                        order.mpesa_ref,
                        download_url,
                        item_type=order.item_type,
                    )
                    logger.info(f"M-Pesa callback - Confirmation email sent for order {order.id}.")
                except Exception:
                    logger.exception("Failed to send payment confirmation email")
        else:
            order.status = "failed"
            db.commit()
            logger.warning(f"M-Pesa callback - Payment failed for order {order.id}. ResultCode: {result_code}")
    except Exception as e:
        logger.error(f"M-Pesa callback processing error: {str(e)}", exc_info=True)

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

    file_to_download = None
    item_name = "item"

    if order.item_type == "product" and order.product_id:
        product = db.query(Product).filter(Product.id == order.product_id).first()
        if product and product.file_path:
            file_to_download = product.file_path
            item_name = product.name
    elif order.item_type == "course" and order.course_id:
        # For courses, you might have a specific downloadable asset or grant access.
        # If courses have a file_path, retrieve it here.
        # For now, let's assume courses don't have a direct download file via this route.
        raise HTTPException(status_code=400, detail="Course access is not via direct download link.")

    if not file_to_download:
        raise HTTPException(status_code=404, detail="Downloadable file not found for this order.")

    # file_path is stored as a URL path like /uploads/products/file.zip
    # strip the leading slash so Path resolves relative to the backend working directory
    actual_file_path = Path(file_to_download.lstrip('/'))
    if not actual_file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server.")

    order.download_used = True # Mark download as used
    db.commit()

    media_type, _ = mimetypes.guess_type(str(actual_file_path))
    return FileResponse(
        path=str(actual_file_path),
        filename=item_name.replace(' ', '_') + actual_file_path.suffix,
        media_type=media_type or "application/octet-stream",
    )
