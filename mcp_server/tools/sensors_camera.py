# mcp_server/tools/cameras.py
"""
Camera management tools using FastAPI backend
"""
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from mcp_server.server import mcp
from mcp_server.api_client import api_client


@mcp.tool()
async def list_cameras(
    tenant_id: str,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200,  # Changed to 200 (API max) from 100
    offset: int = 0,
    include_counts: bool = True,
) -> Dict[str, Any]:
    """
    List camera assets for a tenant with optional site / gateway scoping
    and basic filtering.

    This tool calls the FastAPI endpoint: GET /assets
    
    Uses UPDATED asset model:
      - asset_info.type == "CAMERA"
      - status field for camera status
      - location field (if present)
    
    Args:
        tenant_id: Tenant identifier (required)
        site_id: Optional site filter
        gateway_id: Optional gateway filter
        location: Optional location substring filter (not supported by API, applied locally)
        status: Optional status filter
        limit: Maximum number of results (default: 200, max: 200)
        offset: Pagination offset (default: 0)
        include_counts: Whether to include total count (default: True)
    
    Returns:
        Dict containing:
            - cameras: List of camera assets
            - total: Total count (if include_counts=True)
            - limit: Applied limit
            - offset: Applied offset
    """
    
    # Build query parameters for the API endpoint
    # Note: We don't send asset_type filter to API since it's nested in asset_info.type
    # We'll filter client-side instead
    params = {
        "tenant_id": tenant_id,
    }
    
    # Add optional filters
    if site_id is not None:
        params["site_id"] = site_id
    
    if gateway_id is not None:
        params["gateway_id"] = gateway_id
    
    if status is not None:
        params["status"] = status
    
    try:
        # Call the API /assets endpoint
        import time
        print(f"[DEBUG list_cameras] Calling API with params: {params}")
        start_time = time.time()
        response = await api_client.get("/assets", params=params)
        elapsed = time.time() - start_time
        print(f"[DEBUG list_cameras] API response received in {elapsed:.2f}s")
        print(f"[DEBUG list_cameras] API response: {response}")
     
        # Extract items from the response (handle both 'data' and 'items' keys)
        all_assets = response.get("data") or response.get("items") or []
        print(f"[DEBUG list_cameras] Got {len(all_assets)} assets from API")
        
        # Filter for cameras only (asset_type CAMERA is in asset_info.type)
        # For now, return all assets and filter by type
        cameras = []
        for asset in all_assets:
            asset_info = asset.get("asset_info", {})
            asset_type = asset_info.get("asset_type") or asset_info.get("type")
            if asset_type == "CAMERA" or asset_type is None:  # Include if type is CAMERA or missing
                cameras.append(asset)
        
        print(f"[DEBUG list_cameras] Filtered to {len(cameras)} cameras")
        
        # Apply location filter locally if provided
        if location is not None:
            loc_lower = location.lower()
            cameras = [
                c for c in cameras 
                if loc_lower in c.get("location", "").lower()
            ]
        
        # Apply pagination
        paginated_cameras = cameras[offset:offset + limit]
        total = len(cameras) if include_counts else None
        
        print(f"[DEBUG list_cameras] Returning {len(paginated_cameras)} cameras")
        
        # Return in the expected format
        return {
            "cameras": paginated_cameras,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    except Exception as e:
        # Return error information in a structured way  
        import traceback
        print(f"[DEBUG list_cameras] ERROR: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        return {
            "cameras": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
async def create_camera(
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    name: str,
    rtsp_url: str,
    onvif_url: str,
    location: Optional[str] = None,
    zone: Optional[str] = None,
    status: str = "INACTIVE",
    resolution: str = "1920x1080",
    fps: int = 10,
    userid: Optional[str] = None,
    password: Optional[str] = None,
    capabilities: Optional[list[str]] = None,
    assigned_model_id: Optional[str] = None,
    target_profile_ids: Optional[list[str]] = None,
    assigned_policy_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Create a new camera asset.
    
    This tool calls the FastAPI endpoint: POST /assets
    
    Args:
        camera_id: Unique camera identifier (e.g., "CAM_GATE3_001")
        tenant_id: Tenant identifier
        site_id: Site identifier
        gateway_id: Gateway identifier
        name: Human-readable camera name
        rtsp_url: RTSP stream URL (e.g., "rtsp://user:pass@10.0.0.10/stream1")
        onvif_url: ONVIF URL (e.g., "http://10.0.0.10:8000")
        location: Optional location description
        zone: Optional zone identifier
        status: Camera status (default: "INACTIVE")
        resolution: Video resolution (default: "1920x1080")
        fps: Frames per second (default: 10)
        userid: Optional camera authentication username
        password: Optional camera authentication password
        capabilities: List of capabilities (default: ["VIDEO_STREAM", "OBJECT_DETECTION"])
        assigned_model_id: Optional AI model ID
        target_profile_ids: Optional list of detection profile IDs
        assigned_policy_id: Optional alert policy ID
        tags: Optional list of tags
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - camera: Created camera object (if successful)
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # Set defaults
    if capabilities is None:
        capabilities = ["VIDEO_STREAM", "OBJECT_DETECTION"]
    if target_profile_ids is None:
        target_profile_ids = []
    if tags is None:
        tags = []
    
    # Build the camera payload according to the AssetCreate schema
    payload = {
        "_id": camera_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "name": name,
        "location": location,
        "zone": zone,
        "status": status,
        "asset_info": {
            "type": "CAMERA",
            "capabilities": capabilities,
            "camera": {
                "stream": {
                    "rtsp_url": rtsp_url,
                    "onvif_url": onvif_url,
                    "fps": fps
                },
                "resolution": resolution,
                "userid": userid,
                "password": password
            },
            "bindings": {
                "assigned_model_id": assigned_model_id,
                "target_profile_ids": target_profile_ids,
                "assigned_policy_id": assigned_policy_id
            },
            "tags": tags
        }
    }
    
    try:
        # Call the FastAPI POST /assets endpoint
        response = await api_client.post("/assets", json=payload)
        
        return {
            "success": True,
            "camera": response,
            "message": f"Camera '{camera_id}' created successfully"
        }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        
        # Check for common error cases
        if "409" in error_msg or "already exists" in error_msg.lower():
            return {
                "success": False,
                "error": f"Camera '{camera_id}' already exists",
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
async def update_camera(
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    name: Optional[str] = None,
    location: Optional[str] = None,
    zone: Optional[str] = None,
    status: Optional[str] = None,
    rtsp_url: Optional[str] = None,
    onvif_url: Optional[str] = None,
    fps: Optional[int] = None,
    resolution: Optional[str] = None,
    userid: Optional[str] = None,
    password: Optional[str] = None,
    tags: Optional[list[str]] = None,
    assigned_model_id: Optional[str] = None,
    target_profile_ids: Optional[list[str]] = None,
    assigned_policy_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update camera asset details.
    
    This tool calls the FastAPI endpoint: PUT /assets/{camera_id}
    
    Validates that the camera belongs to the specified tenant/site/gateway before updating.
    All parameters except camera_id, tenant_id, site_id, and gateway_id are optional.
    Only provided fields will be updated.
    
    Args:
        camera_id: Unique camera identifier (e.g., "CAM_GATE3_001")
        tenant_id: Tenant identifier (required for validation)
        site_id: Site identifier (required for validation)
        gateway_id: Gateway identifier (required for validation)
        name: Optional new camera name
        location: Optional new location description
        zone: Optional new zone identifier
        status: Optional new status (e.g., "ACTIVE", "INACTIVE", "MAINTENANCE")
        rtsp_url: Optional new RTSP stream URL
        onvif_url: Optional new ONVIF URL
        fps: Optional new frames per second
        resolution: Optional new video resolution (e.g., "1920x1080")
        userid: Optional new camera authentication username
        password: Optional new camera authentication password
        tags: Optional new list of tags (replaces existing tags)
        assigned_model_id: Optional AI model ID to assign
        target_profile_ids: Optional list of detection profile IDs (replaces existing)
        assigned_policy_id: Optional alert policy ID to assign
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - camera: Updated camera object (if successful)
            - message: Success message
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # First, validate that the camera belongs to the specified tenant/site/gateway
    try:
        existing_camera = await api_client.get(f"/assets/{camera_id}")
        
        # Verify tenant_id matches
        if existing_camera.get("tenant_id") != tenant_id:
            return {
                "success": False,
                "error": f"Camera '{camera_id}' does not belong to tenant '{tenant_id}'",
                "error_type": "ValidationError"
            }
        
        # Verify site_id matches
        if existing_camera.get("site_id") != site_id:
            return {
                "success": False,
                "error": f"Camera '{camera_id}' does not belong to site '{site_id}'",
                "error_type": "ValidationError"
            }
        
        # Verify gateway_id matches
        if existing_camera.get("gateway_id") != gateway_id:
            return {
                "success": False,
                "error": f"Camera '{camera_id}' does not belong to gateway '{gateway_id}'",
                "error_type": "ValidationError"
            }
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            return {
                "success": False,
                "error": f"Camera '{camera_id}' not found",
                "error_type": "NotFoundError"
            }
        # Re-raise other errors to be caught by outer exception handler
        raise
    
    # Build update payload with only provided fields
    payload = {}
    
    # Top-level fields
    if name is not None:
        payload["name"] = name
    if location is not None:
        payload["location"] = location
    if zone is not None:
        payload["zone"] = zone
    if status is not None:
        payload["status"] = status
    
    # Nested asset_info fields
    asset_info_update = {}
    
    # Camera stream updates
    if rtsp_url is not None or onvif_url is not None or fps is not None:
        stream_update = {}
        if rtsp_url is not None:
            stream_update["rtsp_url"] = rtsp_url
        if onvif_url is not None:
            stream_update["onvif_url"] = onvif_url
        if fps is not None:
            stream_update["fps"] = fps
        
        camera_update = {"stream": stream_update}
        if resolution is not None:
            camera_update["resolution"] = resolution
        if userid is not None:
            camera_update["userid"] = userid
        if password is not None:
            camera_update["password"] = password
        
        asset_info_update["camera"] = camera_update
    elif resolution is not None or userid is not None or password is not None:
        camera_update = {}
        if resolution is not None:
            camera_update["resolution"] = resolution
        if userid is not None:
            camera_update["userid"] = userid
        if password is not None:
            camera_update["password"] = password
        asset_info_update["camera"] = camera_update
    
    # Tags update
    if tags is not None:
        asset_info_update["tags"] = tags
    
    # Bindings update
    if assigned_model_id is not None or target_profile_ids is not None or assigned_policy_id is not None:
        bindings_update = {}
        if assigned_model_id is not None:
            bindings_update["assigned_model_id"] = assigned_model_id
        if target_profile_ids is not None:
            bindings_update["target_profile_ids"] = target_profile_ids
        if assigned_policy_id is not None:
            bindings_update["assigned_policy_id"] = assigned_policy_id
        
        asset_info_update["bindings"] = bindings_update
    
    # Add asset_info to payload if there are any updates
    if asset_info_update:
        payload["asset_info"] = asset_info_update
    
    # Check if there's anything to update
    if not payload:
        return {
            "success": False,
            "error": "No fields provided for update",
            "error_type": "ValidationError"
        }
    
    try:
        # Call the FastAPI PUT /assets/{camera_id} endpoint
        response = await api_client.put(f"/assets/{camera_id}", json=payload)
        
        return {
            "success": True,
            "camera": response,
            "message": f"Camera '{camera_id}' updated successfully"
        }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        
        # Check for common error cases
        if "404" in error_msg or "not found" in error_msg.lower():
            return {
                "success": False,
                "error": f"Camera '{camera_id}' not found",
                "error_type": "NotFoundError"
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }


@mcp.tool()
async def delete_camera(
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str
) -> Dict[str, Any]:
    """
    Delete a camera asset by ID.
    
    This tool:
    1. Validates that the camera belongs to the specified tenant/site/gateway
    2. Calls the FastAPI endpoint: DELETE /assets/{camera_id} to delete the camera
    3. Calls HMI Mapper: POST /api/delete-camera to clean up legacy sensor data
    
    Args:
        camera_id: Unique camera identifier to delete (e.g., "CAM_GATE3_001")
        tenant_id: Tenant identifier (required for validation)
        site_id: Site identifier (required for validation)
        gateway_id: Gateway identifier (required for validation)
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - sensor_deleted: Boolean indicating if sensor was deleted from legacy system
            - deleted_from: List of collections deleted from
            - message: Success message (if successful)
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    try:
        # First, validate that the camera belongs to the specified tenant/site/gateway
        try:
            existing_camera = await api_client.get(f"/assets/{camera_id}")
            
            # Verify tenant_id matches
            if existing_camera.get("tenant_id") != tenant_id:
                return {
                    "success": False,
                    "error": f"Camera '{camera_id}' does not belong to tenant '{tenant_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify site_id matches
            if existing_camera.get("site_id") != site_id:
                return {
                    "success": False,
                    "error": f"Camera '{camera_id}' does not belong to site '{site_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify gateway_id matches
            if existing_camera.get("gateway_id") != gateway_id:
                return {
                    "success": False,
                    "error": f"Camera '{camera_id}' does not belong to gateway '{gateway_id}'",
                    "error_type": "ValidationError"
                }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Camera '{camera_id}' not found",
                    "error_type": "NotFoundError"
                }
            # Re-raise other errors to be caught by outer exception handler
            raise
        
        # Validation passed, proceed with deletion
        # First delete from main API
        # Call the FastAPI DELETE /assets/{camera_id} endpoint
        success = await api_client.delete(f"/assets/{camera_id}")
        
        if not success:
            return {
                "success": False,
                "error": "Delete operation did not return expected status",
                "error_type": "UnexpectedResponseError"
            }
        
        # After successfully deleting camera, clean up legacy sensor data
        sensor_deleted = False
        deleted_from = []
        sensor_error = None
        
        try:
            from mcp_server.hmi_mapper_client import hmi_mapper_client
            
            # Call HMI Mapper to delete sensor from all collections
            sensor_result = await hmi_mapper_client.delete_camera(camera_id)
            
            if sensor_result.get("success"):
                sensor_deleted = True
                deleted_from = sensor_result.get("deleted_from", [])
                print(f"? Deleted sensor data for camera '{camera_id}' from: {deleted_from}")
            else:
                sensor_error = sensor_result.get("error", "Unknown error")
                print(f"? Failed to delete sensor data: {sensor_error}")
                
        except Exception as e:
            sensor_error = str(e)
            print(f"? Failed to delete sensor data for camera '{camera_id}': {sensor_error}")
        
        return {
            "success": True,
            "sensor_deleted": sensor_deleted,
            "deleted_from": deleted_from,
            "message": f"Camera '{camera_id}' deleted successfully" +
                      (f" (sensor data deleted from {len(deleted_from)} collections)" if sensor_deleted else "")
        }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        
        # Check for common error cases
        if "404" in error_msg or "not found" in error_msg.lower():
            return {
                "success": False,
                "error": f"Camera '{camera_id}' not found",
                "error_type": "NotFoundError"
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }


@mcp.tool()
async def activate_camera(
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str
) -> Dict[str, Any]:
    """
    Activate a camera by mapping it to the legacy DT_ConfigStorage format.
    
    This tool:
    1. Fetches the camera asset from the HMI database via API
    2. Fetches the associated policy and profile data
    3. Fetches all personnel referenced in the policy
    4. Calls HMI Mapper with complete data to create legacy sensor
    
    The HMI Mapper performs the following operations:
    1. Generates a primary subscriber with tel prefix
    2. Creates the primary subscriber in iota-e/user-data collection
    3. Resolves alert subscribers from policy PERSON targets
    4. Creates alert subscribers in iota-e/user-data collection
    5. Resolves safety labels from profile targets
    6. Transforms and upserts sensor to DT_ConfigStorage/sensors collection
    
    Args:
        camera_id: Unique camera identifier (e.g., "CAM_GATE3_001")
        tenant_id: Tenant identifier
        site_id: Site identifier
        gateway_id: Gateway identifier
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - sensor_id: Created sensor ID (if successful)
            - subscriber_ids: List of subscriber IDs created (if successful)
            - message: Success message
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    try:
        # Step 1: Fetch asset from HMI database via API
        asset = await api_client.get(f"/assets/{camera_id}")
        if not asset:
            return {
                "success": False,
                "error": f"Camera '{camera_id}' not found in HMI database",
                "error_type": "NotFoundError"
            }
        
        # Step 2: Extract policy and profile IDs from asset bindings
        bindings = asset.get("asset_info", {}).get("bindings", {})
        policy_id = bindings.get("assigned_policy_id")
        profile_ids = bindings.get("target_profile_ids", [])
        profile_id = profile_ids[0] if profile_ids else None
        
        if not policy_id:
            return {
                "success": False,
                "error": f"Camera '{camera_id}' missing required field: asset_info.bindings.assigned_policy_id",
                "error_type": "ValidationError"
            }
        
        if not profile_id:
            return {
                "success": False,
                "error": f"Camera '{camera_id}' missing required field: asset_info.bindings.target_profile_ids[0]",
                "error_type": "ValidationError"
            }
        
        # Step 3: Fetch policy data
        policy = await api_client.get(f"/policies/{policy_id}")
        if not policy:
            return {
                "success": False,
                "error": f"Policy '{policy_id}' not found in HMI database",
                "error_type": "NotFoundError"
            }
        
        # Step 4: Fetch profile data
        profile = await api_client.get(f"/profiles/{profile_id}")
        if not profile:
            return {
                "success": False,
                "error": f"Profile '{profile_id}' not found in HMI database",
                "error_type": "NotFoundError"
            }
        
        # Step 5: Extract PERSON targets from policy routes
        person_ids = []
        routes = policy.get("routes", [])
        for route in routes:
            targets = route.get("targets", [])
            for target in targets:
                if target.get("target_type") == "PERSON":
                    person_id = target.get("value")
                    if person_id and person_id not in person_ids:
                        person_ids.append(person_id)
        
        # Step 6: Fetch all personnel documents
        personnel_data = []
        for person_id in person_ids:
            try:
                personnel = await api_client.get(f"/personnel/{person_id}")
                if personnel:
                    personnel_data.append(personnel)
                else:
                    print(f"? Personnel '{person_id}' not found, skipping")
            except Exception as e:
                print(f"? Failed to fetch personnel '{person_id}': {e}")
        
        # Step 7: Call HMI Mapper with complete data
        from mcp_server.hmi_mapper_client import hmi_mapper_client
        
        result = await hmi_mapper_client.map_asset(
            asset_data=asset,
            policy_data=policy,
            profile_data=profile,
            personnel_data=personnel_data
        )
        
        # Check if the mapping was successful
        if result.get("success"):
            return {
                "success": True,
                "sensor_id": result.get("sensor_id"),
                "subscriber_ids": result.get("subscriber_ids", []),
                "message": f"Camera '{camera_id}' started successfully and mapped to sensor '{result.get('sensor_id')}'"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error occurred during camera mapping"),
                "error_type": "MappingError"
            }
    
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors from the API or HMI Mapper service
        error_msg = str(e)
        
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"Resource not found: {error_msg}",
                "error_type": "NotFoundError"
            }
        elif e.response.status_code == 400:
            # Try to extract error details from response
            try:
                error_detail = e.response.json().get("detail", error_msg)
            except:
                error_detail = error_msg
            return {
                "success": False,
                "error": f"Invalid request: {error_detail}",
                "error_type": "ValidationError"
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {error_msg}",
                "error_type": "HTTPError"
            }
    
    except httpx.RequestError as e:
        # Handle connection errors
        return {
            "success": False,
            "error": f"Failed to connect to service: {str(e)}",
            "error_type": "ConnectionError"
        }
    
    except Exception as e:
        # Handle any other unexpected errors
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@mcp.tool()
async def disable_ppe(
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str
) -> Dict[str, Any]:
    """
    Disable PPE monitoring for a camera.
    
    This tool:
    1. Validates that the camera belongs to the specified tenant/site/gateway
    2. Updates camera status to INACTIVE via HMI API
    3. Calls HMI Mapper to clean up legacy sensor and subscriber data
    
    Args:
        camera_id: Unique camera identifier (e.g., "CAM_GATE3_001")
        tenant_id: Tenant identifier (required for validation)
        site_id: Site identifier (required for validation)
        gateway_id: Gateway identifier (required for validation)
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - camera_id: Camera ID
            - status_updated: Boolean indicating if camera status was updated
            - sensor_deleted: Boolean indicating if sensor was deleted from legacy system
            - deleted_from: List of collections deleted from
            - message: Success message (if successful)
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    try:
        # Step 1: Validate that the camera belongs to the specified tenant/site/gateway
        try:
            existing_camera = await api_client.get(f"/assets/{camera_id}")
            
            # Verify tenant_id matches
            if existing_camera.get("tenant_id") != tenant_id:
                return {
                    "success": False,
                    "error": f"Camera '{camera_id}' does not belong to tenant '{tenant_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify site_id matches
            if existing_camera.get("site_id") != site_id:
                return {
                    "success": False,
                    "error": f"Camera '{camera_id}' does not belong to site '{site_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify gateway_id matches
            if existing_camera.get("gateway_id") != gateway_id:
                return {
                    "success": False,
                    "error": f"Camera '{camera_id}' does not belong to gateway '{gateway_id}'",
                    "error_type": "ValidationError"
                }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Camera '{camera_id}' not found",
                    "error_type": "NotFoundError"
                }
            # Re-raise other errors to be caught by outer exception handler
            raise
        
        # Step 2: Update camera status to INACTIVE
        status_updated = False
        try:
            update_res = await api_client.put(
                f"/assets/{camera_id}",
                json={"status": "INACTIVE"}
            )
            status_updated = True
            print(f"? Updated camera status to INACTIVE: {camera_id}")
        except Exception as e:
            print(f"? Failed to update camera status: {e}")
            # Continue with sensor cleanup even if status update fails
        
        # Step 3: Clean up legacy sensor and subscriber data
        sensor_deleted = False
        deleted_from = []
        sensor_error = None
        
        try:
            from mcp_server.hmi_mapper_client import hmi_mapper_client
            
            # Call HMI Mapper to disable PPE (delete sensor and subscriber)
            sensor_result = await hmi_mapper_client.disable_ppe(camera_id)
            
            if sensor_result.get("success"):
                sensor_deleted = True
                deleted_from = sensor_result.get("deleted_from", [])
                print(f"? Disabled PPE for camera '{camera_id}', deleted from: {deleted_from}")
            else:
                sensor_error = sensor_result.get("error", "Unknown error")
                print(f"? Failed to disable PPE: {sensor_error}")
                
        except Exception as e:
            sensor_error = str(e)
            print(f"? Failed to disable PPE for camera '{camera_id}': {sensor_error}")
        
        # Determine overall success
        overall_success = status_updated or sensor_deleted
        
        return {
            "success": overall_success,
            "camera_id": camera_id,
            "status_updated": status_updated,
            "sensor_deleted": sensor_deleted,
            "deleted_from": deleted_from,
            "message": f"PPE monitoring disabled for camera '{camera_id}'" +
                      (f" (status updated to INACTIVE)" if status_updated else "") +
                      (f" (sensor data deleted from {len(deleted_from)} collections)" if sensor_deleted else ""),
            "warning": sensor_error if sensor_error and overall_success else None
        }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        
        # Check for common error cases
        if "404" in error_msg or "not found" in error_msg.lower():
            return {
                "success": False,
                "error": f"Camera '{camera_id}' not found",
                "error_type": "NotFoundError"
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }
