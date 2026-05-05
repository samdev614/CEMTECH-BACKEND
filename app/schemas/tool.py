from pydantic import BaseModel
from datetime import datetime

class ToolOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    category: str | None
    external_url: str | None
    cover_image: str | None
    is_published: bool
    is_featured: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
