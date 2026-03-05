from typing import TypedDict, List, Dict, Any, Optional

class PPEConfigState(TypedDict, total=False):
    # Input
    tenant_id: str
    site_id: str
    gateway_id: str
    location_filter: str
    sensor_status: str

    # Intermediate
    cameras: List[Dict[str, Any]]
    camera_ids: List[str]
    ppe_profile: Optional[Dict[str, Any]]
    ppe_model: Optional[Dict[str, Any]]
    policy: Optional[Dict[str, Any]]

    # Results
    assigned_profile_cameras: List[str]
    assigned_model_cameras: List[str]
    assigned_policy_cameras: List[str]
    
    # Camera activation results
    status_updated_cameras: List[str]      # Cameras set to ACTIVE status
    status_update_failed: List[str]        # Cameras that failed status update
    mapping_activated_cameras: List[str]   # Cameras mapped to legacy format
    mapping_activation_failed: List[str]   # Cameras that failed legacy mapping

    # Status
    status: Optional[str]
    error_reason: Optional[str]
