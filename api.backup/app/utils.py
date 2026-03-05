from datetime import datetime, timezone
from typing import Any, Dict


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def set_created_updated(doc: Dict[str, Any]) -> Dict[str, Any]:
    now = utc_now()
    doc.setdefault("created_at", now)
    doc["updated_at"] = now
    return doc


def set_updated(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc["updated_at"] = utc_now()
    return doc


def mongo_sanitize(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure datetime fields are returned as-is (FastAPI serializes),
    and prevent accidental ObjectId leakage (your _id is string-based).
    """
    return doc


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary into dot notation for MongoDB $set operations.
    
    Example:
        {'asset_info': {'camera': {'stream': {'fps': 30}}}}
        becomes
        {'asset_info.camera.stream.fps': 30}
    
    This ensures partial updates merge with existing data instead of replacing entire objects.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict) and v:  # Only flatten non-empty dicts
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
