from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db import get_db
from app.crud.base import CRUDBase
from app.schemas.models import ModelCreate, ModelUpdate, ModelOut
from app.schemas.common import ListResponse

router = APIRouter(prefix="/models", tags=["models"])
crud = CRUDBase("models")

@router.post("", response_model=ModelOut, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
async def create_model(payload: ModelCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    if await crud.get(db, payload.id):
        raise HTTPException(status_code=409, detail="Model already exists")
    return await crud.create(db, payload.dict(by_alias=True))

@router.get("/{model_id}", response_model=ModelOut, response_model_by_alias=True)
async def get_model(model_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.get(db, model_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Model not found")
    return doc

@router.put("/{model_id}", response_model=ModelOut, response_model_by_alias=True)
async def update_model(model_id: str, payload: ModelUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.update(db, model_id, payload.dict(exclude_unset=True))
    if not doc:
        raise HTTPException(status_code=404, detail="Model not found")
    return doc

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    ok = await crud.delete(db, model_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Model not found")
    return None

@router.get("", response_model=ListResponse)
async def list_models(
    tenant_id: str | None = None,
    site_id: str | None = None,
    gateway_id: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    framework_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    q = {}
    if tenant_id: q["tenant_id"] = tenant_id
    if site_id: q["site_id"] = site_id
    if gateway_id: q["gateway_id"] = gateway_id
    if status_filter: q["status"] = status_filter
    if framework_id: q["framework_id"] = framework_id
    total, items = await crud.list(db, q, limit=limit, offset=offset)
    return {"total": total, "items": items, "limit": limit, "offset": offset}
