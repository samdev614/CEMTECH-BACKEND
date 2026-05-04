from pydantic import BaseModel

class ServiceMediaOut(BaseModel):
    key: str
    media_url: str | None
    media_type: str

    model_config = {"from_attributes": True}
