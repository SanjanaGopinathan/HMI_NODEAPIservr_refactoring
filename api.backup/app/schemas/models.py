from pydantic import BaseModel, Field
from app.schemas.common import Timestamps


class ModelCreate(BaseModel):
    class Config:
        extra = "forbid"
    id: str = Field(..., alias="_id", description="Model ID e.g. MODEL_PPE_YOLOV12")
    tenant_id: str
    site_id: str
    gateway_id: str
    name: str
    framework_id: str
    Supported_Profile_ids: list[str] = []
    status: str = "ACTIVE"


class ModelUpdate(BaseModel):
    class Config:
        extra = "forbid"
    name: str | None = None
    framework_id: str | None = None
    Supported_Profile_ids: list[str] | None = None
    status: str | None = None


class ModelOut(ModelCreate, Timestamps):
    class Config:
        extra = "ignore"
