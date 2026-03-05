from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db import get_db
from app.crud.base import CRUDBase
from app.schemas.assets import AssetCreate, AssetUpdate, AssetOut
from app.schemas.common import ListResponse

router = APIRouter(prefix="/assets", tags=["assets"])
crud = CRUDBase("assets")


@router.post("", response_model=AssetOut, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
async def create_asset(payload: AssetCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    existing = await crud.get(db, payload.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Asset '{payload.id}' already exists")
    return await crud.create(db, payload.dict(by_alias=True))


@router.get("/{asset_id}", response_model=AssetOut, response_model_by_alias=True)
async def get_asset(asset_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.get(db, asset_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Asset not found")
    return doc


@router.put("/{asset_id}", response_model=AssetOut, response_model_by_alias=True)
async def update_asset(asset_id: str, payload: AssetUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.update(db, asset_id, payload.dict(exclude_unset=True))
    if not doc:
        raise HTTPException(status_code=404, detail="Asset not found")
    return doc


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(asset_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    ok = await crud.delete(db, asset_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Asset not found")
    return None


@router.get("", response_model=ListResponse)
async def list_assets(
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    asset_type: Optional[str] = Query(None, description="CAMERA/SENSOR (asset_info.type)"),
    tag: Optional[str] = Query(None, description="Match a tag in asset_info.tags"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    q = {}
    if tenant_id:
        q["tenant_id"] = tenant_id
    if site_id:
        q["site_id"] = site_id
    if gateway_id:
        q["gateway_id"] = gateway_id
    if status_filter:
        q["status"] = status_filter
    if asset_type:
        q["asset_info.type"] = asset_type
    if tag:
        q["asset_info.tags"] = tag  # array contains

    total, items = await crud.list(db, q, limit=limit, offset=offset, sort=[("updated_at", -1)])
    return {"total": total, "items": items, "limit": limit, "offset": offset}
