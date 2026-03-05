# mcp_server/tools/detection.py
"""
Detection profile management tools using FastAPI backend
"""
from typing import Dict, Any, Optional, List
from mcp_server.server import mcp
from mcp_server.api_client import api_client


@mcp.tool()
async def list_profiles(
    tenant_id: str,
    site_id: Optional[str] = None,
    target_name_contains: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List detection profiles for a tenant with optional filtering.
    
    This tool calls the FastAPI endpoint: GET /profiles
    
    Args:
        tenant_id: Tenant identifier (required)
        site_id: Optional site filter
        target_name_contains: Optional filter to match profile name or targets
    
    Returns:
        Dict containing:
            - detection_profiles: List of profile objects
            - count: Total number of profiles
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # Build query parameters for the FastAPI endpoint
    params = {
        "tenant_id": tenant_id,
        "limit": 200,  # Get all profiles
        "offset": 0,
    }
    
    # Add optional filters
    if site_id is not None:
        params["site_id"] = site_id
    
    if target_name_contains:
        params["target"] = target_name_contains
    
    try:
        # Call the FastAPI GET /profiles endpoint
        response = await api_client.get("/profiles", params=params)
        
        # Extract items from the response
        profiles = response.get("items", [])
        total = response.get("total", 0)
        
        # Return in the expected format
        return {
            "detection_profiles": profiles,
            "count": total
        }
    
    except Exception as e:
        # Return error information in a structured way
        return {
            "detection_profiles": [],
            "count": 0,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@mcp.tool()
async def assign_profile(
    tenant_id: str,
    camera_ids: List[str],
    target_profile_ids: List[str],
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    mode: str = "MERGE",
) -> Dict[str, Any]:
    """
    Assign detection profiles to camera assets.
    
    This tool:
    1. Lists cameras via GET /assets with filters
    2. Updates each camera via PUT /assets/{camera_id}
    
    Updates: asset_info.bindings.target_profile_ids
    
    Args:
        tenant_id: Tenant identifier (required)
        camera_ids: List of camera IDs to assign profiles to
        target_profile_ids: List of detection profile IDs to assign
        site_id: Optional site filter
        gateway_id: Optional gateway filter
        mode: "MERGE" (default) or "REPLACE" - how to handle existing profiles
    
    Returns:
        Dict containing:
            - status: "ok" or "error"
            - updated_camera_ids: List of successfully updated camera IDs
            - mode: The mode used (MERGE or REPLACE)
            - requested_target_profile_ids: The profile IDs that were assigned
            - not_found_camera_ids: List of camera IDs that weren't found
            - error: Error message (if status is "error")
    """
    
    mode_u = (mode or "").upper().strip()
    if mode_u not in {"MERGE", "REPLACE"}:
        return {"status": "error", "error": f"Invalid mode: {mode}"}
    
    camera_id_set = set(camera_ids or [])
    requested_profiles = list(dict.fromkeys([pid for pid in (target_profile_ids or []) if pid]))
    
    updated_ids: List[str] = []
    not_found_camera_ids: List[str] = []
    
    try:
        # Step 1: Get cameras matching the filters
        params = {
            "tenant_id": tenant_id,
            "asset_type": "CAMERA",
            "limit": 200,
            "offset": 0,
        }
        
        if site_id is not None:
            params["site_id"] = site_id
        
        if gateway_id is not None:
            params["gateway_id"] = gateway_id
        
        response = await api_client.get("/assets", params=params)
        cameras = response.get("items", [])
        
        # Filter to only cameras in camera_ids list
        scoped_camera_ids = set()
        cameras_to_update = []
        
        for camera in cameras:
            cam_id = camera.get("_id")
            if not cam_id:
                continue
            
            scoped_camera_ids.add(cam_id)
            
            if cam_id in camera_id_set:
                cameras_to_update.append(camera)
        
        # Step 2: Update each camera with the detection profiles
        for camera in cameras_to_update:
            cam_id = camera.get("_id")
            
            try:
                # Get existing profile IDs
                existing_profiles = camera.get("asset_info", {}).get("bindings", {}).get("target_profile_ids", [])
                
                # Calculate new profile IDs based on mode
                if mode_u == "REPLACE":
                    new_profiles = requested_profiles
                else:  # MERGE
                    # Combine existing and new, removing duplicates while preserving order
                    new_profiles = list(dict.fromkeys(list(existing_profiles) + requested_profiles))
                
                # Build update payload
                update_payload = {
                    "asset_info": {
                        "bindings": {
                            "target_profile_ids": new_profiles
                        }
                    }
                }
                
                # Update the camera
                await api_client.put(f"/assets/{cam_id}", json=update_payload)
                updated_ids.append(cam_id)
                
            except Exception as e:
                # If update fails for this camera, log it but continue with others
                print(f"Warning: Failed to update camera {cam_id}: {e}")
                continue
        
        # Step 3: Identify cameras that weren't found
        for cid in camera_id_set:
            if cid not in scoped_camera_ids:
                not_found_camera_ids.append(cid)
        
        return {
            "status": "ok",
            "updated_camera_ids": updated_ids,
            "mode": mode_u,
            "requested_target_profile_ids": requested_profiles,
            "not_found_camera_ids": not_found_camera_ids,
        }
    
    except Exception as e:
        # Return error information in a structured way
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "updated_camera_ids": updated_ids,  # Return what was updated before error
            "not_found_camera_ids": not_found_camera_ids,
        }


@mcp.tool()
async def create_profile(
    profile_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    name: str,
    targets: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a new detection profile.
    
    This tool calls the FastAPI endpoint: POST /profiles
    
    Args:
        profile_id: Unique profile identifier (e.g., "PROFILE_PPE_001")
        tenant_id: Tenant identifier
        site_id: Site identifier
        gateway_id: Gateway identifier
        name: Human-readable profile name
        targets: List of detection targets (e.g., ["helmet", "vest", "person"])
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - profile: Created profile object (if successful)
            - message: Success message
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # Set defaults
    if targets is None:
        targets = []
    
    # Build the profile payload according to the ProfileCreate schema
    payload = {
        "_id": profile_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "name": name,
        "targets": targets,
    }
    
    try:
        # Call the FastAPI POST /profiles endpoint
        response = await api_client.post("/profiles", json=payload)
        
        return {
            "success": True,
            "profile": response,
            "message": f"Profile '{profile_id}' created successfully"
        }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        
        # Check for common error cases
        if "409" in error_msg or "already exists" in error_msg.lower():
            return {
                "success": False,
                "error": f"Profile '{profile_id}' already exists",
                "error_type": "ConflictError"
            }
        elif "404" in error_msg:
            return {
                "success": False,
                "error": "API endpoint not found",
                "error_type": "NotFoundError"
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }


@mcp.tool()
async def delete_profile(
    profile_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str
) -> Dict[str, Any]:
    """
    Delete a detection profile by ID.
    
    This tool calls the FastAPI endpoint: DELETE /profiles/{profile_id}
    
    Validates that the profile belongs to the specified tenant/site/gateway before deletion.
    
    Args:
        profile_id: Unique profile identifier to delete (e.g., "PROFILE_PPE_001")
        tenant_id: Tenant identifier (required for validation)
        site_id: Site identifier (required for validation)
        gateway_id: Gateway identifier (required for validation)
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - message: Success message (if successful)
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    try:
        # First, validate that the profile belongs to the specified tenant/site/gateway
        try:
            existing_profile = await api_client.get(f"/profiles/{profile_id}")
            
            # Verify tenant_id matches
            if existing_profile.get("tenant_id") != tenant_id:
                return {
                    "success": False,
                    "error": f"Profile '{profile_id}' does not belong to tenant '{tenant_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify site_id matches
            if existing_profile.get("site_id") != site_id:
                return {
                    "success": False,
                    "error": f"Profile '{profile_id}' does not belong to site '{site_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify gateway_id matches
            if existing_profile.get("gateway_id") != gateway_id:
                return {
                    "success": False,
                    "error": f"Profile '{profile_id}' does not belong to gateway '{gateway_id}'",
                    "error_type": "ValidationError"
                }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Profile '{profile_id}' not found",
                    "error_type": "NotFoundError"
                }
            # Re-raise other errors to be caught by outer exception handler
            raise
        
        # Validation passed, proceed with deletion
        # Call the FastAPI DELETE /profiles/{profile_id} endpoint
        success = await api_client.delete(f"/profiles/{profile_id}")
        
        if success:
            return {
                "success": True,
                "message": f"Profile '{profile_id}' deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": "Delete operation did not return expected status",
                "error_type": "UnexpectedResponseError"
            }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        
        # Check for common error cases
        if "404" in error_msg or "not found" in error_msg.lower():
            return {
                "success": False,
                "error": f"Profile '{profile_id}' not found",
                "error_type": "NotFoundError"
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }
