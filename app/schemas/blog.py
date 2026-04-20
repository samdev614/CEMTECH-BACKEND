from pydantic import BaseModel
from datetime import datetime

class BlogPostCreate(BaseModel):
    title: str
    slug: str
    excerpt: str | None = None
    content: str
    category: str | None = None
    tags: str | None = None
    is_published: bool = False
    read_time: int = 5

class BlogPostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    excerpt: str | None = None
    content: str | None = None
    category: str | None = None
    tags: str | None = None
    is_published: bool | None = None
    read_time: int | None = None

class BlogPostOut(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str | None
    content: str
    cover_image: str | None
    category: str | None
    tags: str | None
    is_published: bool
    read_time: int
    created_at: datetime
    updated_at: datetime | None
    published_at: datetime | None

    model_config = {"from_attributes": True}
