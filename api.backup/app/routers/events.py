from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db import get_db
from app.crud.base import CRUDBase
from app.schemas.events import EventCreate, EventUpdate, EventOut
from app.schemas.common import ListResponse

router = APIRouter(prefix="/events", tags=["events"])
crud = CRUDBase("events")

@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
async def create_event(payload: EventCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    if await crud.get(db, payload.id):
        raise HTTPException(status_code=409, detail="Event already exists")
    # events sample did not include created/updated; we still store created_at/updated_at is optional,
    # but we keep event as-is; CRUDBase will add created_at/updated_at only if provided.
    return await crud.create(db, payload.dict(by_alias=True))

@router.get("/{event_id}", response_model=EventOut, response_model_by_alias=True)
async def get_event(event_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.get(db, event_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Event not found")
    return doc

@router.put("/{event_id}", response_model=EventOut, response_model_by_alias=True)
async def update_event(event_id: str, payload: EventUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.update(db, event_id, payload.dict(exclude_unset=True))
    if not doc:
        raise HTTPException(status_code=404, detail="Event not found")
    return doc

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    ok = await crud.delete(db, event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Event not found")
    return None

@router.get("", response_model=ListResponse)
async def list_events(
    tenant_id: str | None = None,
    site_id: str | None = None,
    gateway_id: str | None = None,
    sensor_id: str | None = None,
    anomaly_type: str | None = None,
    severity: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    q = {}
    if tenant_id: q["tenant_id"] = tenant_id
    if site_id: q["site_id"] = site_id
    if gateway_id: q["gateway_id"] = gateway_id
    if sensor_id: q["sensor_id"] = sensor_id
    if anomaly_type: q["anomaly_type"] = anomaly_type
    if severity: q["severity"] = severity
    if status_filter: q["status"] = status_filter
    total, items = await crud.list(db, q, limit=limit, offset=offset, sort=[("detected_at", -1)])
    return {"total": total, "items": items, "limit": limit, "offset": offset}
