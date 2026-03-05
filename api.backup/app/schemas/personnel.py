from pydantic import BaseModel, Field
from app.schemas.common import Timestamps


class ContactInfo(BaseModel):
    class Config:
        extra = "forbid"
    phone: str | None = None
    email: str | None = None
    sip_uri: str | None = None


class PersonnelCreate(BaseModel):
    class Config:
        extra = "forbid"
    id: str = Field(..., alias="_id", description="Personnel ID e.g. P_SUPERVISOR_1")
    tenant_id: str
    site_id: str
    name: str
    role: str
    contact: ContactInfo = Field(default_factory=ContactInfo)
    on_call: bool = False
    status: str = "ACTIVE"


class PersonnelUpdate(BaseModel):
    class Config:
        extra = "forbid"
    name: str | None = None
    role: str | None = None
    contact: ContactInfo | None = None
    on_call: bool | None = None
    status: str | None = None


class PersonnelOut(PersonnelCreate, Timestamps):
    pass
