from pydantic import BaseModel, Field
from app.schemas.common import Timestamps


class PolicyTarget(BaseModel):
    class Config:
        extra = "forbid"
    target_type: str = Field(..., description="ROLE or PERSON")
    value: str


class PolicyRoute(BaseModel):
    class Config:
        extra = "forbid"
    severity: str
    targets: list[PolicyTarget] = []
    channels: list[str] = []


class PolicyCreate(BaseModel):
    class Config:
        extra = "forbid"
    id: str = Field(..., alias="_id", description="Policy ID e.g. POLICY_PPE_SITE_01_0001")
    tenant_id: str
    site_id: str
    anomaly_type: str
    min_severity: str = "WARNING"
    enabled: bool = True
    priority: int = 100
    routes: list[PolicyRoute] = []


class PolicyUpdate(BaseModel):
    class Config:
        extra = "forbid"
    anomaly_type: str | None = None
    min_severity: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    routes: list[PolicyRoute] | None = None


class PolicyOut(PolicyCreate, Timestamps):
    class Config:
        extra = "ignore"
