# mcp_server/tools/models.py
"""
Model management tools using FastAPI backend
"""
from typing import Dict, Any, Optional, List
from mcp_server.server import mcp
from mcp_server.api_client import api_client


@mcp.tool()
async def list_models(
    tenant_id: str,
    site_id: Optional[str] = None,
    framework_id: Optional[str] = None,
    status: str = "ACTIVE",
) -> Dict[str, Any]:
    """
    List CV models for a tenant with optional filtering.
    
    This tool calls the FastAPI endpoint: GET /models
    
    Args:
        tenant_id: Tenant identifier (required)
        site_id: Optional site filter
        framework_id: Optional framework filter (e.g., "openvino-2024.1")
        status: Status filter (default: "ACTIVE")
    
    Returns:
        Dict containing:
            - models: List of model objects
            - count: Total number of models
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # Build query parameters for the FastAPI endpoint
    params = {
        "tenant_id": tenant_id,
        "limit": 200,  # Get all models
        "offset": 0,
    }
    
    # Add optional filters
    if site_id is not None:
        params["site_id"] = site_id
    
    if framework_id:
        params["framework_id"] = framework_id
    
    if status:
        params["status"] = status
    
    try:
        # Call the FastAPI GET /models endpoint
        response = await api_client.get("/models", params=params)
        
        # Extract items from the response
        models = response.get("items", [])
        total = response.get("total", 0)
        
        # Return in the expected format
        return {
            "models": models,
            "count": total
        }
    
    except Exception as e:
        # Return error information in a structured way
        return {
            "models": [],
            "count": 0,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@mcp.tool()
async def assign_cameras_to_model(
    tenant_id: str,
    camera_ids: List[str],
    model_id: str,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    auto_adjust_stream_profile: bool = True,
) -> Dict[str, Any]:
    """
    Assign camera assets to the given model.
    
    This tool:
    1. Verifies the model exists via GET /models/{model_id}
    2. Lists cameras via GET /assets with filters
    3. Updates each camera via PUT /assets/{camera_id}
    
    Updates: asset_info.bindings.assigned_model_id
    
    Args:
        tenant_id: Tenant identifier (required)
        camera_ids: List of camera IDs to assign
        model_id: Model ID to assign cameras to
        site_id: Optional site filter
        gateway_id: Optional gateway filter
        auto_adjust_stream_profile: Whether to adjust stream profile (currently no-op)
    
    Returns:
        Dict containing:
            - status: "ok" or "error"
            - assigned_camera_ids: List of successfully assigned camera IDs
            - model_id: The model ID
            - auto_adjust_stream_profile: Whether auto-adjust was enabled
            - not_found_camera_ids: List of camera IDs that weren't found
            - error: Error message (if status is "error")
    """
    
    assigned: List[str] = []
    not_found_camera_ids: List[str] = []
    camera_id_set = set(camera_ids or [])
    
    try:
        # Step 1: Verify that model exists for the tenant
        try:
            model = await api_client.get(f"/models/{model_id}")
            
            # Verify tenant matches
            if model.get("tenant_id") != tenant_id:
                return {
                    "status": "error",
                    "error": f"Model '{model_id}' does not belong to tenant '{tenant_id}'"
                }
            
            # Verify site matches if provided
            if site_id is not None and model.get("site_id") != site_id:
                return {
                    "status": "error",
                    "error": f"Model '{model_id}' not found for tenant '{tenant_id}', site '{site_id}'"
                }
                
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "status": "error",
                    "error": f"Model '{model_id}' not found for tenant '{tenant_id}'"
                          + (f", site '{site_id}'" if site_id else "")
                }
            raise  # Re-raise other errors
        
        # Step 2: Get cameras matching the filters
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
        
        # Step 3: Update each camera with the assigned model
        for camera in cameras_to_update:
            cam_id = camera.get("_id")
            
            try:
                # Build update payload
                # We need to update asset_info.bindings.assigned_model_id
                update_payload = {
                    "asset_info": {
                        "bindings": {
                            "assigned_model_id": model_id
                        }
                    }
                }
                
                # Update the camera
                await api_client.put(f"/assets/{cam_id}", json=update_payload)
                assigned.append(cam_id)
                
            except Exception as e:
                # If update fails for this camera, log it but continue with others
                print(f"Warning: Failed to update camera {cam_id}: {e}")
                continue
        
        # Step 4: Identify cameras that weren't found
        for cid in camera_id_set:
            if cid not in scoped_camera_ids:
                not_found_camera_ids.append(cid)
        
        return {
            "status": "ok",
            "assigned_camera_ids": assigned,
            "model_id": model_id,
            "auto_adjust_stream_profile": bool(auto_adjust_stream_profile),
            "not_found_camera_ids": not_found_camera_ids,
        }
    
    except Exception as e:
        # Return error information in a structured way
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "assigned_camera_ids": assigned,  # Return what was assigned before error
            "not_found_camera_ids": not_found_camera_ids,
        }


@mcp.tool()
async def create_model(
    model_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    name: str,
    framework_id: str,
    supported_profile_ids: Optional[List[str]] = None,
    status: str = "ACTIVE",
) -> Dict[str, Any]:
    """
    Create a new AI model.
    
    This tool calls the FastAPI endpoint: POST /models
    
    Args:
        model_id: Unique model identifier (e.g., "MODEL_PPE_YOLOV12")
        tenant_id: Tenant identifier
        site_id: Site identifier
        gateway_id: Gateway identifier where model is deployed
        name: Human-readable model name
        framework_id: Framework identifier (e.g., "openvino-2024.1", "tensorflow", "pytorch")
        supported_profile_ids: List of detection profile IDs this model supports
        status: Model status (default: "ACTIVE")
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - model: Created model object (if successful)
            - message: Success message
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # Set defaults
    if supported_profile_ids is None:
        supported_profile_ids = []
    
    # Build the model payload according to the ModelCreate schema
    payload = {
        "_id": model_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "name": name,
        "framework_id": framework_id,
        "Supported_Profile_ids": supported_profile_ids,
        "status": status
    }
    
    try:
        # Call the FastAPI POST /models endpoint
        response = await api_client.post("/models", json=payload)
        
        return {
            "success": True,
            "model": response,
            "message": f"Model '{model_id}' created successfully"
        }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        
        # Check for common error cases
        if "409" in error_msg or "already exists" in error_msg.lower():
            return {
                "success": False,
                "error": f"Model '{model_id}' already exists",
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
async def delete_model(
    model_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str
) -> Dict[str, Any]:
    """
    Delete an AI model by ID.
    
    This tool calls the FastAPI endpoint: DELETE /models/{model_id}
    
    Validates that the model belongs to the specified tenant/site/gateway before deletion.
    
    Args:
        model_id: Unique model identifier to delete (e.g., "MODEL_PPE_YOLOV12")
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
        # First, validate that the model belongs to the specified tenant/site/gateway
        try:
            existing_model = await api_client.get(f"/models/{model_id}")
            
            # Verify tenant_id matches
            if existing_model.get("tenant_id") != tenant_id:
                return {
                    "success": False,
                    "error": f"Model '{model_id}' does not belong to tenant '{tenant_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify site_id matches
            if existing_model.get("site_id") != site_id:
                return {
                    "success": False,
                    "error": f"Model '{model_id}' does not belong to site '{site_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify gateway_id matches
            if existing_model.get("gateway_id") != gateway_id:
                return {
                    "success": False,
                    "error": f"Model '{model_id}' does not belong to gateway '{gateway_id}'",
                    "error_type": "ValidationError"
                }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Model '{model_id}' not found",
                    "error_type": "NotFoundError"
                }
            # Re-raise other errors to be caught by outer exception handler
            raise
        
        # Validation passed, proceed with deletion
        # Call the FastAPI DELETE /models/{model_id} endpoint
        success = await api_client.delete(f"/models/{model_id}")
        
        if success:
            return {
                "success": True,
                "message": f"Model '{model_id}' deleted successfully"
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
                "error": f"Model '{model_id}' not found",
                "error_type": "NotFoundError"
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }
