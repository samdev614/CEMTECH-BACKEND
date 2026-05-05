from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class PresetOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    category: str | None
    price: Decimal
    cover_image: str | None
    file_path: str | None
    is_published: bool
    is_featured: bool
    sort_order: int
    sales_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
