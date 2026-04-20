from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.product import Product, Order
from app.schemas.product import ProductOut, OrderOut
from app.services.upload import save_image, save_product_file

router = APIRouter()

@router.get("/", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db), category: str = None):
    q = db.query(Product).filter(Product.is_published == True)
    if category:
        q = q.filter(Product.category == category)
    return q.order_by(Product.sort_order.asc(), Product.created_at.desc()).all()

@router.get("/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug, Product.is_published == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/admin/all", response_model=List[ProductOut])
def admin_list_products(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Product).order_by(Product.sort_order.asc()).all()

@router.post("/admin/", response_model=ProductOut)
async def create_product(
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(None),
    category: str = Form(None),
    price: Decimal = Form(...),
    is_published: bool = Form(False),
    is_featured: bool = Form(False),
    sort_order: int = Form(0),
    cover_image: UploadFile = File(None),
    product_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if db.query(Product).filter(Product.slug == slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    image_path = await save_image(cover_image) if cover_image else None
    file_path  = await save_product_file(product_file) if product_file else None

    product = Product(
        name=name, slug=slug, description=description, category=category,
        price=price, is_published=is_published, is_featured=is_featured,
        sort_order=sort_order, cover_image=image_path, file_path=file_path,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.patch("/admin/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    name: str = Form(None),
    slug: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    price: Decimal = Form(None),
    is_published: bool = Form(None),
    is_featured: bool = Form(None),
    sort_order: int = Form(None),
    cover_image: UploadFile = File(None),
    product_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in dict(
        name=name, slug=slug, description=description, category=category,
        price=price, is_published=is_published, is_featured=is_featured, sort_order=sort_order,
    ).items():
        if value is not None:
            setattr(product, field, value)

    if cover_image:
        product.cover_image = await save_image(cover_image)
    if product_file:
        product.file_path = await save_product_file(product_file)

    db.commit()
    db.refresh(product)
    return product

@router.delete("/admin/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Deleted"}

@router.get("/admin/orders/all", response_model=List[OrderOut])
def admin_list_orders(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Order).order_by(Order.created_at.desc()).all()
