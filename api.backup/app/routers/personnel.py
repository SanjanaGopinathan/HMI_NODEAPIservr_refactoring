from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db import get_db
from app.crud.base import CRUDBase
from app.schemas.personnel import PersonnelCreate, PersonnelUpdate, PersonnelOut
from app.schemas.common import ListResponse

router = APIRouter(prefix="/personnel", tags=["personnel"])
crud = CRUDBase("personnel")

@router.post("", response_model=PersonnelOut, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
async def create_personnel(payload: PersonnelCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    if await crud.get(db, payload.id):
        raise HTTPException(status_code=409, detail="Personnel already exists")
    return await crud.create(db, payload.dict(by_alias=True))

@router.get("/{person_id}", response_model=PersonnelOut, response_model_by_alias=True)
async def get_personnel(person_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.get(db, person_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Personnel not found")
    return doc

@router.put("/{person_id}", response_model=PersonnelOut, response_model_by_alias=True)
async def update_personnel(person_id: str, payload: PersonnelUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await crud.update(db, person_id, payload.dict(exclude_unset=True))
    if not doc:
        raise HTTPException(status_code=404, detail="Personnel not found")
    return doc

@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personnel(person_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    ok = await crud.delete(db, person_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Personnel not found")
    return None

@router.get("", response_model=ListResponse)
async def list_personnel(
    tenant_id: str | None = None,
    site_id: str | None = None,
    role: str | None = None,
    on_call: bool | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    q = {}
    if tenant_id: q["tenant_id"] = tenant_id
    if site_id: q["site_id"] = site_id
    if role: q["role"] = role
    if on_call is not None: q["on_call"] = on_call
    if status_filter: q["status"] = status_filter
    total, items = await crud.list(db, q, limit=limit, offset=offset)
    return {"total": total, "items": items, "limit": limit, "offset": offset}
