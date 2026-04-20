from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    category: str | None = None
    price: Decimal
    is_published: bool = False
    is_featured: bool = False
    sort_order: int = 0

class ProductUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    category: str | None = None
    price: Decimal | None = None
    is_published: bool | None = None
    is_featured: bool | None = None
    sort_order: int | None = None

class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    category: str | None
    price: Decimal
    cover_image: str | None
    file_path: str | None
    is_published: bool
    is_featured: bool
    sort_order: int
    sales_count: int
    created_at: datetime

    model_config = {"from_attributes": True}

class OrderOut(BaseModel):
    id: int
    product_id: int
    customer_name: str | None
    customer_email: str | None
    customer_phone: str | None
    amount: Decimal
    status: str
    mpesa_ref: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
