from datetime import datetime
from pydantic import BaseModel, Field


class MongoBase(BaseModel):
    class Config:
        extra = "forbid"

    id: str = Field(..., alias="_id")

class WithTenantSite(BaseModel):
    tenant_id: str
    site_id: str

class WithGateway(WithTenantSite):
    gateway_id: str

class Timestamps(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None

class ListResponse(BaseModel):
    total: int
    items: list
    limit: int
    offset: int
