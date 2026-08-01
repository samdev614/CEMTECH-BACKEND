from datetime import datetime

from pydantic import BaseModel


class GalleryItemOut(BaseModel):
    id: int
    title: str
    category: str | None
    alt_text: str | None
    image_url: str
    is_published: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
