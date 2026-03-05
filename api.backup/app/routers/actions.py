from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db import get_db
from app.crud.base import CRUDBase
from app.schemas.actions import ActionCreate, ActionUpdate, ActionOut
from app.schemas.common import ListResponse

router = APIRouter(prefix="/actions", tags=["actions"])
crud = CRUDBase("actions")

@router.post("", response_model=ActionOut, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
async def create_action(payload: ActionCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    if await crud.get(db, payload.id):
        raise HTTPException(status_code=409, detail="Action already exists")
    return await crud.create(db, payload.dict(by_alias=True))

@router.get("/{action_id}", response_model=ActionOut, response_model_by_alias=True)
async def get_action(action_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.get(db, action_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Action not found")
    return doc

@router.put("/{action_id}", response_model=ActionOut, response_model_by_alias=True)
async def update_action(action_id: str, payload: ActionUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.update(db, action_id, payload.dict(exclude_unset=True))
    if not doc:
        raise HTTPException(status_code=404, detail="Action not found")
    return doc

@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(action_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    ok = await crud.delete(db, action_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Action not found")
    return None

@router.get("", response_model=ListResponse)
async def list_actions(
    tenant_id: str | None = None,
    site_id: str | None = None,
    gateway_id: str | None = None,
    event_id: str | None = None,
    policy_id: str | None = None,
    route_severity: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    q = {}
    if tenant_id: q["tenant_id"] = tenant_id
    if site_id: q["site_id"] = site_id
    if gateway_id: q["gateway_id"] = gateway_id
    if event_id: q["event_id"] = event_id
    if policy_id: q["policy_id"] = policy_id
    if route_severity: q["route_severity"] = route_severity
    total, items = await crud.list(db, q, limit=limit, offset=offset)
    return {"total": total, "items": items, "limit": limit, "offset": offset}
