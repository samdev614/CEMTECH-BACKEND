from pydantic import BaseModel, Field
from datetime import datetime


class DocumentationCreate(BaseModel):
    title: str
    slug: str
    summary: str | None = None
    content: str
    section: str | None = None
    sort_order: int = 0
    is_published: bool = False


class DocumentationUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    summary: str | None = None
    content: str | None = None
    section: str | None = None
    sort_order: int | None = None
    is_published: bool | None = None


class DocumentationOut(BaseModel):
    id: int
    title: str
    slug: str
    summary: str | None = Field(None, validation_alias="excerpt")
    content: str
    cover_image: str | None
    section: str | None = Field(None, validation_alias="category")
    sort_order: int = 0
    is_published: bool
    created_at: datetime
    updated_at: datetime | None
    published_at: datetime | None

    model_config = {"from_attributes": True, "populate_by_name": True}
