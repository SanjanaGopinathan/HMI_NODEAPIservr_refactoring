from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from app.utils import set_created_updated, set_updated, mongo_sanitize, flatten_dict


class CRUDBase:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def col(self, db: AsyncIOMotorDatabase):
        return db[self.collection_name]

    async def create(self, db: AsyncIOMotorDatabase, doc: Dict[str, Any]) -> Dict[str, Any]:
        doc = set_created_updated(doc)
        await self.col(db).insert_one(doc)
        return mongo_sanitize(doc)

    async def get(self, db: AsyncIOMotorDatabase, _id: str) -> Optional[Dict[str, Any]]:
        doc = await self.col(db).find_one({"_id": _id})
        return mongo_sanitize(doc) if doc else None

    async def update(self, db: AsyncIOMotorDatabase, _id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        patch = {k: v for k, v in patch.items() if v is not None}
        if not patch:
            return await self.get(db, _id)
        
        # Flatten nested dicts to dot notation for proper merging
        patch = flatten_dict(patch)
        patch = set_updated(patch)
        
        result = await self.col(db).update_one(
            {"_id": _id},
            {"$set": patch}
        )
        
        if result.matched_count == 0:
            return None
            
        # Fetch the full updated document
        doc = await self.col(db).find_one({"_id": _id})
        return mongo_sanitize(doc) if doc else None

    async def delete(self, db: AsyncIOMotorDatabase, _id: str) -> bool:
        res = await self.col(db).delete_one({"_id": _id})
        return res.deleted_count == 1

    async def list(
        self,
        db: AsyncIOMotorDatabase,
        query: Dict[str, Any],
        limit: int = 50,
        offset: int = 0,
        sort: list[tuple[str, int]] | None = None,
    ) -> tuple[int, list[Dict[str, Any]]]:
        sort = sort or [("updated_at", -1)]
        total = await self.col(db).count_documents(query)
        cursor = self.col(db).find(query).sort(sort).skip(offset).limit(limit)
        items = [mongo_sanitize(d) async for d in cursor]
        return total, items
