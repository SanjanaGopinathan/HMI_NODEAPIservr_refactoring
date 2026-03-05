from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db import get_db
from app.crud.base import CRUDBase
from app.schemas.gateway import GatewayCreate, GatewayUpdate, GatewayOut
from app.schemas.common import ListResponse

router = APIRouter(prefix="/gateway", tags=["gateway"])
crud = CRUDBase("gateway")


@router.post("", response_model=GatewayOut, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
async def create_gateway(payload: GatewayCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    existing = await crud.get(db, payload.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Gateway '{payload.id}' already exists")
    return await crud.create(db, payload.dict(by_alias=True))


@router.get("/{gateway_id}", response_model=GatewayOut, response_model_by_alias=True)
async def get_gateway(gateway_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.get(db, gateway_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return doc


@router.put("/{gateway_id}", response_model=GatewayOut, response_model_by_alias=True)
async def update_gateway(gateway_id: str, payload: GatewayUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.update(db, gateway_id, payload.dict(exclude_unset=True))
    if not doc:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return doc


@router.delete("/{gateway_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gateway(gateway_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    ok = await crud.delete(db, gateway_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return None


@router.get("", response_model=ListResponse)
async def list_gateways(
    tenant_id: str | None = None,
    site_id: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    q = {}
    if tenant_id:
        q["tenant_id"] = tenant_id
    if site_id:
        q["site_id"] = site_id
    if status_filter:
        q["status"] = status_filter

    total, items = await crud.list(db, q, limit=limit, offset=offset, sort=[("updated_at", -1)])
    return {"total": total, "items": items, "limit": limit, "offset": offset}
