from pydantic import BaseModel
from datetime import datetime

class ProjectCreate(BaseModel):
    title: str
    slug: str
    description: str | None = None
    use_case: str | None = None
    category: str | None = None
    tags: str | None = None
    gallery_images: list[str] | None = None
    live_url: str | None = None
    video_url: str | None = None
    source_url: str | None = None
    is_featured: bool = False
    is_published: bool = True
    sort_order: int = 0

class ProjectUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    use_case: str | None = None
    category: str | None = None
    tags: str | None = None
    gallery_images: list[str] | None = None
    live_url: str | None = None
    video_url: str | None = None
    source_url: str | None = None
    is_featured: bool | None = None
    is_published: bool | None = None
    sort_order: int | None = None

class ProjectOut(BaseModel):
    id: int
    title: str
    slug: str
    description: str | None
    use_case: str | None
    category: str | None
    tags: str | None
    cover_image: str | None
    gallery_images: list[str] | None = None
    live_url: str | None
    video_url: str | None
    source_url: str | None
    is_featured: bool
    is_published: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
