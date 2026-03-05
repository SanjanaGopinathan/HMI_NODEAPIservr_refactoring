from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import Timestamps


class GatewayHMI(BaseModel):
    class Config:
        extra = "forbid"
    base_url: str
    health_path: str = "/health"
    user_id: str | None = None
    password: str | None = None


class GatewayCreate(BaseModel):
    class Config:
        extra = "forbid"
    id: str = Field(..., alias="_id", description="Gateway ID (string) e.g. GW_SITE_01_0001")
    tenant_id: str
    site_id: str
    name: str
    hmi: GatewayHMI
    status: str = "ONLINE"
    last_seen_at: datetime | None = None
    capabilities: list[str] = []


class GatewayUpdate(BaseModel):
    class Config:
        extra = "forbid"
    name: str | None = None
    hmi: GatewayHMI | None = None
    status: str | None = None
    last_seen_at: datetime | None = None
    capabilities: list[str] | None = None


class GatewayOut(GatewayCreate, Timestamps):
    pass
