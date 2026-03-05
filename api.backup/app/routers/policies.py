from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db import get_db
from app.crud.base import CRUDBase
from app.schemas.policies import PolicyCreate, PolicyUpdate, PolicyOut
from app.schemas.common import ListResponse

router = APIRouter(prefix="/policies", tags=["policies"])
crud = CRUDBase("policies")

@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
async def create_policy(payload: PolicyCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    if await crud.get(db, payload.id):
        raise HTTPException(status_code=409, detail="Policy already exists")
    return await crud.create(db, payload.dict(by_alias=True))

@router.get("/{policy_id}", response_model=PolicyOut, response_model_by_alias=True)
async def get_policy(policy_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.get(db, policy_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Policy not found")
    return doc

@router.put("/{policy_id}", response_model=PolicyOut, response_model_by_alias=True)
async def update_policy(policy_id: str, payload: PolicyUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.update(db, policy_id, payload.dict(exclude_unset=True))
    if not doc:
        raise HTTPException(status_code=404, detail="Policy not found")
    return doc

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    ok = await crud.delete(db, policy_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Policy not found")
    return None

@router.get("", response_model=ListResponse)
async def list_policies(
    tenant_id: str | None = None,
    site_id: str | None = None,
    anomaly_type: str | None = None,
    enabled: bool | None = None,
    min_severity: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    q = {}
    if tenant_id: q["tenant_id"] = tenant_id
    if site_id: q["site_id"] = site_id
    if anomaly_type: q["anomaly_type"] = anomaly_type
    if enabled is not None: q["enabled"] = enabled
    if min_severity: q["min_severity"] = min_severity
    total, items = await crud.list(db, q, limit=limit, offset=offset)
    return {"total": total, "items": items, "limit": limit, "offset": offset}
