from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import Timestamps


class Detection(BaseModel):
    class Config:
        extra = "forbid"
    label: str
    confidence: float


class EventRaw(BaseModel):
    class Config:
        extra = "forbid"
    model_id: str | None = None
    detections: list[Detection] = []


class EventCreate(BaseModel):
    class Config:
        extra = "forbid"
    id: str = Field(..., alias="_id", description="Event ID e.g. EVT_20251215_000001")
    tenant_id: str
    site_id: str
    gateway_id: str
    sensor_id: str
    anomaly_type: str
    severity: str
    detected_at: datetime
    raw: EventRaw = Field(default_factory=EventRaw)
    status: str = "OPEN"


class EventUpdate(BaseModel):
    class Config:
        extra = "forbid"
    severity: str | None = None
    status: str | None = None
    raw: EventRaw | None = None
    detected_at: datetime | None = None


class EventOut(EventCreate, Timestamps):
    class Config:
        extra = "ignore"
