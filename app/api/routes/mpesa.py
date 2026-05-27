import secrets
import mimetypes
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from app.models.product import Product, Order
from app.models.course import Course # Import Course model
from app.models.enrollment import Enrollment # Import Enrollment
from app.schemas.product import OrderOut
from app.core.security import get_current_user
from app.services.mpesa import stk_push
from app.services.email import send_payment_confirmation
from app.core.config import settings

logger = logging.getLogger(__name__)

# Mounted under /api/products
buy_router = APIRouter()

# Mounted under /api  (avoids slug collision with /{slug})
util_router = APIRouter()


class BuyRequest(BaseModel):
    name: str
    email: str
    phone: str


@buy_router.post("/{slug}/buy", response_model=OrderOut)
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
        raise HTTPException(status_code=502, detail=f"M-Pesa push failed: {str(e)}")

    return order


@buy_router.post("/courses/{slug}/buy", response_model=OrderOut) # New endpoint for courses
async def buy_course(slug: str, body: BuyRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    course = db.query(Course).filter(Course.slug == slug, Course.is_published == True).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Create an order for the course
    order = Order(
        course_id=course.id, # Link to course
        user_id=current_user.id if current_user else None,
        item_type="course", # Specify item type
        customer_name=body.name,
        customer_email=body.email,
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

            item_name = "Your purchase"
            download_file_path = None

            if order.item_type == "product" and order.product_id:
                product = db.query(Product).filter(Product.id == order.product_id).first()
                if product:
                    product.sales_count = (product.sales_count or 0) + 1
                    item_name = product.name
                    download_file_path = product.file_path
            elif order.item_type == "course" and order.course_id:
                course = db.query(Course).filter(Course.id == order.course_id).first()
                if course:
                    item_name = course.title
                    
                    # Automatically enroll the user if logged in
                    if order.user_id:
                        enrollment = db.query(Enrollment).filter(
                            Enrollment.user_id == order.user_id,
                            Enrollment.course_id == order.course_id
                        ).first()
                        
                        if not enrollment:
                            enrollment = Enrollment(
                                user_id=order.user_id,
                                course_id=order.course_id,
                                price_paid=order.amount,
                                status="active",
                                payment_status="paid"
                            )
                            db.add(enrollment)
                        else:
                            enrollment.status = "active"
                            enrollment.payment_status = "paid"

            db.commit()
            base_url = settings.MPESA_CALLBACK_URL.split('/api/')[0]
            download_url = f"{base_url}/api/download/{order.download_token}"
            try:
                send_payment_confirmation(
                    order.customer_name, order.customer_email,
                    item_name, order.mpesa_ref, download_url,
                )
            except Exception:
                logger.exception("Failed to send payment confirmation email")
        else:
            order.status = "failed"
            db.commit()
    except Exception as e:
        logger.error(f"M-Pesa callback processing error: {str(e)}")

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
