from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(300), nullable=False)
    slug         = Column(String(300), unique=True, index=True, nullable=False)
    description  = Column(Text)
    category     = Column(String(100))
    price        = Column(Numeric(10, 2), nullable=False)
    cover_image  = Column(String)
    file_path    = Column(String)        # path to the downloadable file
    is_published = Column(Boolean, default=False)
    is_featured  = Column(Boolean, default=False)
    sort_order   = Column(Integer, default=0)
    sales_count  = Column(Integer, default=0)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())


class Order(Base):
    __tablename__ = "orders"

    id           = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(80), unique=True, index=True)
    idempotency_key = Column(String(120), unique=True, index=True)
    product_id   = Column(Integer, ForeignKey("products.id"), nullable=True)
    course_id    = Column(Integer, ForeignKey("courses.id"), nullable=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    item_type    = Column(String(50), nullable=False, default="product") # "product" or "course"
    customer_name  = Column(String(200))
    customer_email = Column(String(200))
    customer_phone = Column(String(50))
    amount       = Column(Numeric(10, 2), nullable=False)
    currency     = Column(String(10), default="KES")
    status       = Column(String(50), default="pending")  # pending, paid, failed
    mpesa_ref    = Column(String(100))
    download_token = Column(String(200))
    download_used  = Column(Boolean, default=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
