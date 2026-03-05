from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import Timestamps


class DecisionTarget(BaseModel):
    class Config:
        extra = "forbid"
    type: str
    value: str


class DecisionAddress(BaseModel):
    class Config:
        extra = "forbid"
    type: str
    address: str


class Decision(BaseModel):
    class Config:
        extra = "forbid"
    channel: str
    target: DecisionTarget
    resolved_person_id: str | None = None
    address: DecisionAddress | None = None
    status: str = "PENDING"
    sent_at: datetime | None = None


class ActionCreate(BaseModel):
    class Config:
        extra = "forbid"
    id: str = Field(..., alias="_id", description="Action ID e.g. ACT_20251215_000001")
    tenant_id: str
    site_id: str
    gateway_id: str
    event_id: str
    policy_id: str
    route_severity: str
    decisions: list[Decision] = []


class ActionUpdate(BaseModel):
    class Config:
        extra = "forbid"
    route_severity: str | None = None
    decisions: list[Decision] | None = None


class ActionOut(ActionCreate, Timestamps):
    pass
