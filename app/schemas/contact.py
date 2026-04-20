from pydantic import BaseModel, EmailStr
from datetime import datetime

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str | None = None
    message: str

class ContactOut(BaseModel):
    id: int
    name: str
    email: str
    subject: str | None
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
