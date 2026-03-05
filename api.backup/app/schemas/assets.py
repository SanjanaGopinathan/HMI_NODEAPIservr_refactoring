from pydantic import BaseModel, Field
from app.schemas.common import Timestamps


class CameraStream(BaseModel):
    class Config:
        extra = "forbid"
    rtsp_url: str
    onvif_url: str
    fps: int = 10


class CameraInfo(BaseModel):
    class Config:
        extra = "forbid"
    stream: CameraStream
    resolution: str = "1920x1080"
    userid: str | None = None
    password: str | None = None


class AssetBindings(BaseModel):
    class Config:
        extra = "forbid"
    assigned_model_id: str | None = None
    target_profile_ids: list[str] = []
    assigned_policy_id: str | None = None


class AssetInfo(BaseModel):
    class Config:
        extra = "forbid"
    type: str = Field(..., description="CAMERA / SENSOR")
    capabilities: list[str] = []
    camera: CameraInfo | None = None
    bindings: AssetBindings = Field(default_factory=AssetBindings)
    tags: list[str] = []


class AssetCreate(BaseModel):
    class Config:
        extra = "forbid"
    id: str = Field(..., alias="_id", description="Asset ID e.g. CAM_GATE3_001")
    tenant_id: str
    site_id: str
    gateway_id: str
    name: str
    location: str | None = None
    zone: str | None = None
    status: str = "ACTIVE"
    asset_info: AssetInfo


# Update models with all optional fields for partial updates
class CameraStreamUpdate(BaseModel):
    class Config:
        extra = "forbid"
    rtsp_url: str | None = None
    onvif_url: str | None = None
    fps: int | None = None


class CameraInfoUpdate(BaseModel):
    class Config:
        extra = "forbid"
    stream: CameraStreamUpdate | None = None
    resolution: str | None = None
    userid: str | None = None
    password: str | None = None


class AssetBindingsUpdate(BaseModel):
    class Config:
        extra = "forbid"
    assigned_model_id: str | None = None
    target_profile_ids: list[str] | None = None
    assigned_policy_id: str | None = None


class AssetInfoUpdate(BaseModel):
    class Config:
        extra = "forbid"
    type: str | None = None
    capabilities: list[str] | None = None
    camera: CameraInfoUpdate | None = None
    bindings: AssetBindingsUpdate | None = None
    tags: list[str] | None = None


class AssetUpdate(BaseModel):
    class Config:
        extra = "forbid"
    name: str | None = None
    location: str | None = None
    zone: str | None = None
    status: str | None = None
    asset_info: AssetInfoUpdate | None = None


class AssetOut(AssetCreate, Timestamps):
    class Config:
        extra = "ignore"
