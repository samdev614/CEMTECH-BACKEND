from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.documentation import Documentation
from app.schemas.documentation import DocumentationCreate, DocumentationUpdate, DocumentationOut
from app.services.upload import save_image

router = APIRouter()


# ── Admin (must come before /{slug} to avoid route shadowing) ────────────────

@router.post("/admin/upload-image")
async def upload_doc_image(
    image: UploadFile = File(...),
    _=Depends(require_admin),
):
    url = await save_image(image)
    return {"url": url}


@router.get("/admin/all", response_model=List[DocumentationOut])
def admin_list_docs(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Documentation).order_by(Documentation.sort_order, Documentation.created_at.desc()).all()


@router.post("/admin/", response_model=DocumentationOut)
def create_doc(
    data: DocumentationCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    if db.query(Documentation).filter(Documentation.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    doc = Documentation(
        title=data.title,
        slug=data.slug,
        content=data.content,
        excerpt=data.summary,
        category=data.section,
        sort_order=data.sort_order,
        is_published=data.is_published,
        author_id=admin.id,
        published_at=datetime.now(timezone.utc) if data.is_published else None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.patch("/admin/{doc_id}", response_model=DocumentationOut)
def update_doc(
    doc_id: int,
    data: DocumentationUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    doc = db.query(Documentation).filter(Documentation.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")

    if data.title is not None:
        doc.title = data.title
    if data.slug is not None:
        doc.slug = data.slug
    if data.content is not None:
        doc.content = data.content
    if data.summary is not None:
        doc.excerpt = data.summary
    if data.section is not None:
        doc.category = data.section
    if data.sort_order is not None:
        doc.sort_order = data.sort_order
    if data.is_published is not None:
        if data.is_published and not doc.is_published:
            doc.published_at = datetime.now(timezone.utc)
        doc.is_published = data.is_published

    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/admin/{doc_id}")
def delete_doc(doc_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    doc = db.query(Documentation).filter(Documentation.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")
    db.delete(doc)
    db.commit()
    return {"message": "Deleted"}


# ── Public (after admin routes) ──────────────────────────────────────────────

@router.get("/", response_model=List[DocumentationOut])
def list_docs(db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    return (
        db.query(Documentation)
        .filter(Documentation.is_published == True)
        .order_by(Documentation.sort_order, Documentation.published_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{slug}", response_model=DocumentationOut)
def get_doc(slug: str, db: Session = Depends(get_db)):
    doc = db.query(Documentation).filter(Documentation.slug == slug, Documentation.is_published == True).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")
    return doc
