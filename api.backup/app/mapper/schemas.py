from typing import List, Optional
from pydantic import BaseModel


class MapAssetRequest(BaseModel):
    """Request to map an HMI asset to legacy format
    
    All HMI data must be provided by the caller to avoid database dependencies.
    The caller should fetch these documents from hmi_db before calling this endpoint.
    """
    asset_data: dict  # Complete asset document from hmi_db.assets
    policy_data: dict  # Complete policy document from hmi_db.policies
    profile_data: dict  # Complete profile document from hmi_db.profiles
    personnel_data: List[dict]  # List of personnel documents for all PERSON targets in policy


class MapAssetResponse(BaseModel):
    """Response from asset mapping"""
    success: bool
    sensor_id: Optional[str] = None
    subscriber_ids: List[str] = []
    error: Optional[str] = None


class CreateSubscriberRequest(BaseModel):
    """Request to create a subscriber from personnel
    
    The caller must provide the complete personnel document from hmi_db.
    """
    personnel_data: dict  # Complete personnel document from hmi_db.personnel
    personnel_id: Optional[str] = None  # Optional, for backward compatibility


class CreateSubscriberResponse(BaseModel):
    """Response from subscriber creation"""
    success: bool
    subscriber_id: Optional[str] = None
    personnel_id: Optional[str] = None
    error: Optional[str] = None


class DeleteSubscriberRequest(BaseModel):
    """Request to delete a subscriber
    
    The caller must provide the complete personnel document from hmi_db.
    """
    personnel_data: dict  # Complete personnel document from hmi_db.personnel
    personnel_id: Optional[str] = None  # Optional, for backward compatibility


class DeleteSubscriberResponse(BaseModel):
    """Response from subscriber deletion"""
    success: bool
    subscriber_id: Optional[str] = None
    personnel_id: Optional[str] = None
    error: Optional[str] = None


class DeleteCameraRequest(BaseModel):
    """Request to delete a camera sensor"""
    camera_id: str


class DeleteCameraResponse(BaseModel):
    """Response from camera deletion"""
    success: bool
    camera_id: Optional[str] = None
    deleted_from: List[str] = []
    error: Optional[str] = None


class DisablePPERequest(BaseModel):
    """Request to disable PPE monitoring for a camera"""
    camera_id: str


class DisablePPEResponse(BaseModel):
    """Response from disabling PPE monitoring"""
    success: bool
    camera_id: Optional[str] = None
    deleted_from: List[str] = []
    error: Optional[str] = None


class MapperConfigRequest(BaseModel):
    """Request to configure HMI Mapper with a specific gateway context"""
    gateway_id: str
