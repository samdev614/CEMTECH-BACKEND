from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.portfolio import Project
from app.core.utils import format_video_embed_url
from app.schemas.portfolio import ProjectOut
from app.services.upload import save_image

router = APIRouter()


async def _save_gallery_images(files: List[UploadFile]) -> list[str]:
    images: list[str] = []
    for file in files:
        if file and file.filename:
            images.append(await save_image(file))
    return images

@router.get("/", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), category: str = None):
    q = db.query(Project).filter(Project.is_published == True)
    if category:
        q = q.filter(Project.category == category)
    return q.order_by(Project.sort_order.asc(), Project.created_at.desc()).all()

@router.get("/{slug}", response_model=ProjectOut)
def get_project(slug: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.slug == slug, Project.is_published == True).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.get("/admin/all", response_model=List[ProjectOut])
def admin_list_projects(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Project).order_by(Project.sort_order.asc()).all()

@router.post("/admin/", response_model=ProjectOut)
async def create_project(
    title: str = Form(...),
    slug: str = Form(...),
    description: str = Form(None),
    use_case: str = Form(None),
    category: str = Form(None),
    tags: str = Form(None),
    live_url: str = Form(None),
    video_url: str = Form(None),
    source_url: str = Form(None),
    is_featured: bool = Form(False),
    is_published: bool = Form(True),
    sort_order: int = Form(0),
    cover_image: UploadFile = File(None),
    gallery_images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if db.query(Project).filter(Project.slug == slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    image_path = await save_image(cover_image) if cover_image else None
    gallery_image_paths = await _save_gallery_images(gallery_images)
    project = Project(
        title=title, slug=slug, description=description, use_case=use_case,
        category=category, tags=tags, live_url=live_url, video_url=format_video_embed_url(video_url),
        source_url=source_url, is_featured=is_featured, is_published=is_published,
        sort_order=sort_order, cover_image=image_path, gallery_images=gallery_image_paths,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.patch("/admin/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    title: str = Form(None),
    slug: str = Form(None),
    description: str = Form(None),
    use_case: str = Form(None),
    category: str = Form(None),
    tags: str = Form(None),
    live_url: str = Form(None),
    video_url: str = Form(None),
    source_url: str = Form(None),
    is_featured: bool = Form(None),
    is_published: bool = Form(None),
    sort_order: int = Form(None),
    cover_image: UploadFile = File(None),
    gallery_images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in dict(
        title=title, slug=slug, description=description, use_case=use_case,
        category=category, tags=tags, live_url=live_url, video_url=format_video_embed_url(video_url),
        source_url=source_url, is_featured=is_featured, is_published=is_published,
        sort_order=sort_order,
    ).items():
        if value is not None:
            setattr(project, field, value)

    if cover_image:
        project.cover_image = await save_image(cover_image)

    new_gallery_images = await _save_gallery_images(gallery_images)
    if new_gallery_images:
        project.gallery_images = [*(project.gallery_images or []), *new_gallery_images]

    db.commit()
    db.refresh(project)
    return project

@router.delete("/admin/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Deleted"}
