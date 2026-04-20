from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.blog import BlogPost
from app.schemas.blog import BlogPostCreate, BlogPostUpdate, BlogPostOut
from app.services.upload import save_image

router = APIRouter()

# ── Public ──────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[BlogPostOut])
def list_posts(db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    return db.query(BlogPost).filter(BlogPost.is_published == True)\
             .order_by(BlogPost.published_at.desc()).offset(skip).limit(limit).all()

@router.get("/{slug}", response_model=BlogPostOut)
def get_post(slug: str, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.slug == slug, BlogPost.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# ── Admin ────────────────────────────────────────────────────────────────────

@router.get("/admin/all", response_model=List[BlogPostOut])
def admin_list_posts(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()

@router.post("/admin/", response_model=BlogPostOut)
async def create_post(
    title: str = Form(...),
    slug: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(None),
    category: str = Form(None),
    tags: str = Form(None),
    is_published: bool = Form(False),
    read_time: int = Form(5),
    cover_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    if db.query(BlogPost).filter(BlogPost.slug == slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    image_path = await save_image(cover_image) if cover_image else None

    post = BlogPost(
        title=title, slug=slug, content=content, excerpt=excerpt,
        category=category, tags=tags, is_published=is_published,
        read_time=read_time, cover_image=image_path, author_id=admin.id,
        published_at=datetime.now(timezone.utc) if is_published else None,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.patch("/admin/{post_id}", response_model=BlogPostOut)
async def update_post(
    post_id: int,
    title: str = Form(None),
    slug: str = Form(None),
    content: str = Form(None),
    excerpt: str = Form(None),
    category: str = Form(None),
    tags: str = Form(None),
    is_published: bool = Form(None),
    read_time: int = Form(None),
    cover_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if title is not None:       post.title = title
    if slug is not None:        post.slug = slug
    if content is not None:     post.content = content
    if excerpt is not None:     post.excerpt = excerpt
    if category is not None:    post.category = category
    if tags is not None:        post.tags = tags
    if read_time is not None:   post.read_time = read_time
    if is_published is not None:
        if is_published and not post.is_published:
            post.published_at = datetime.now(timezone.utc)
        post.is_published = is_published
    if cover_image:
        post.cover_image = await save_image(cover_image)

    db.commit()
    db.refresh(post)
    return post

@router.delete("/admin/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"message": "Deleted"}
