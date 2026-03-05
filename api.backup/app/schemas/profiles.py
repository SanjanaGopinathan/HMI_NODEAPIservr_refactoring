from pydantic import BaseModel, Field
from typing import List
from app.schemas.common import Timestamps


class ProfileCreate(BaseModel):
    class Config:
        extra = "forbid"
    id: str = Field(..., alias="_id", description="Profile ID e.g. PROFILE_PPE_001")
    tenant_id: str
    site_id: str
    gateway_id: str
    name: str
    targets: List[str] = []


class ProfileUpdate(BaseModel):
    class Config:
        extra = "forbid"
    name: str | None = None
    targets: List[str] | None = None


class ProfileOut(ProfileCreate, Timestamps):
    class Config:
        extra = "ignore"
