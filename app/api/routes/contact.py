import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.contact import ContactMessage
from app.schemas.contact import ContactCreate, ContactOut
from app.services.email import send_contact_notification, send_contact_autoreply

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ContactOut)
def submit_contact(data: ContactCreate, db: Session = Depends(get_db)):
    msg = ContactMessage(**data.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    try:
        send_contact_notification(msg.name, msg.email, msg.subject, msg.message)
        send_contact_autoreply(msg.name, msg.email, msg.subject)
    except Exception as exc:
        logger.exception("Failed to send contact notification or auto-reply email")
    return msg

@router.get("/admin/all", response_model=List[ContactOut])
def admin_list_messages(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()

@router.patch("/admin/{msg_id}/read")
def mark_read(msg_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.is_read = True
    db.commit()
    return {"message": "Marked as read"}

@router.delete("/admin/{msg_id}")
def delete_message(msg_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()
    return {"message": "Deleted"}
