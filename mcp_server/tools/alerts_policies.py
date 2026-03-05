# mcp_server/tools/alerts.py
"""
Alert policy management tools using FastAPI backend
"""
from typing import Dict, Any, Optional, List
from mcp_server.server import mcp
from mcp_server.api_client import api_client


@mcp.tool()
async def list_policy(
    tenant_id: str,
    anomaly_type: Optional[str] = None,
    site_id: Optional[str] = None,
    enabled: Optional[bool] = None,
    min_severity: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List alert policies for a tenant with optional filtering.
    
    This tool calls the FastAPI endpoint: GET /policies
    
    Args:
        tenant_id: Tenant identifier (required)
        anomaly_type: Optional anomaly type filter (e.g., "PPE_VIOLATION", "INTRUSION")
        site_id: Optional site filter
        enabled: Optional filter for enabled status
        min_severity: Optional minimum severity filter (e.g., "WARNING", "CRITICAL")
    
    Returns:
        Dict containing:
            - policies: List of policy objects
            - count: Total number of policies
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # Build query parameters for the FastAPI endpoint
    params = {
        "tenant_id": tenant_id,
        "limit": 200,  # Get all policies
        "offset": 0,
    }
    
    # Add optional filters
    if site_id is not None:
        params["site_id"] = site_id
    
    if anomaly_type is not None:
        params["anomaly_type"] = anomaly_type
    
    if enabled is not None:
        params["enabled"] = enabled
    
    if min_severity is not None:
        params["min_severity"] = min_severity
    
    try:
        # Call the FastAPI GET /policies endpoint
        response = await api_client.get("/policies", params=params)
        
        # Extract items from the response
        policies = response.get("items", [])
        total = response.get("total", 0)
        
        # Return in the expected format
        return {
            "policies": policies,
            "count": total
        }
    
    except Exception as e:
        # Return error information in a structured way
        return {
            "policies": [],
            "count": 0,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@mcp.tool()
async def set_alert_policy(
    tenant_id: str,
    camera_ids: List[str],
    policy_id: str,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assign an alert policy to camera assets.
    
    This tool:
    1. Verifies the policy exists via GET /policies/{policy_id}
    2. Lists cameras via GET /assets with filters
    3. Updates each camera via PUT /assets/{camera_id}
    
    Updates: asset_info.bindings.assigned_policy_id
    
    Args:
        tenant_id: Tenant identifier (required)
        camera_ids: List of camera IDs to assign the policy to
        policy_id: Policy ID to assign cameras to
        site_id: Optional site filter
        gateway_id: Optional gateway filter
    
    Returns:
        Dict containing:
            - status: "ok" or "error"
            - assigned_camera_ids: List of successfully assigned camera IDs
            - policy_id: The policy ID
            - not_found_camera_ids: List of camera IDs that weren't found
            - error: Error message (if status is "error")
    """
    
    assigned: List[str] = []
    not_found_camera_ids: List[str] = []
    camera_id_set = set(camera_ids or [])
    
    try:
        # Step 1: Verify that policy exists for the tenant
        try:
            policy = await api_client.get(f"/policies/{policy_id}")
            
            # Verify tenant matches
            if policy.get("tenant_id") != tenant_id:
                return {
                    "status": "error",
                    "error": f"Policy '{policy_id}' does not belong to tenant '{tenant_id}'"
                }
            
            # Verify site matches if provided
            if site_id is not None and policy.get("site_id") != site_id:
                return {
                    "status": "error",
                    "error": f"Policy '{policy_id}' not found for tenant '{tenant_id}', site '{site_id}'"
                }
                
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "status": "error",
                    "error": f"Policy '{policy_id}' not found for tenant '{tenant_id}'"
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
        
        # Step 3: Update each camera with the assigned policy
        for camera in cameras_to_update:
            cam_id = camera.get("_id")
            
            try:
                # Build update payload
                update_payload = {
                    "asset_info": {
                        "bindings": {
                            "assigned_policy_id": policy_id
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
            "policy_id": policy_id,
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
async def create_policy(
    policy_id: str,
    tenant_id: str,
    site_id: str,
    anomaly_type: str,
    severity_levels: List[str],
    channels: List[str],
    person_ids: List[str],
    min_severity: Optional[str] = None,
    enabled: Optional[bool] = None,
    priority: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a new alert policy.
    
    This tool calls the FastAPI endpoint: POST /policies
    
    Args:
        policy_id: Unique policy identifier (e.g., "POLICY_PPE_SITE_01_0001")
        tenant_id: Tenant identifier
        site_id: Site identifier
        anomaly_type: Type of anomaly (e.g., "PPE_VIOLATION", "INTRUSION")
        severity_levels: List of severity levels to route (e.g., ["WARNING", "CRITICAL"])
        channels: List of notification channels (e.g., ["EMAIL", "SIP_PTT", "HMI_POPUP"])
        person_ids: List of person IDs to notify
        min_severity: Minimum severity threshold (default: "WARNING")
        enabled: Whether policy is enabled (default: True)
        priority: Policy priority (default: 100)
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - policy: Created policy object (if successful)
            - message: Success message
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # Apply defaults for optional parameters
    if min_severity is None:
        min_severity = "WARNING"
    if enabled is None:
        enabled = True
    if priority is None:
        priority = 100
    
    # Build routes from severity levels, channels, and person IDs
    routes = []
    for severity in severity_levels:
        targets = [
            {"target_type": "PERSON", "value": person_id}
            for person_id in person_ids
        ]
        routes.append({
            "severity": severity.upper().strip(),
            "targets": targets,
            "channels": [ch.upper().strip() for ch in channels]
        })
    
    # Build the policy payload according to the PolicyCreate schema
    payload = {
        "_id": policy_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "anomaly_type": anomaly_type.upper().strip(),
        "min_severity": min_severity.upper().strip(),
        "enabled": enabled,
        "priority": priority,
        "routes": routes,
    }
    
    # Debug logging
    print(f"[DEBUG] Creating policy with payload: {payload}")
    
    try:
        # Call the FastAPI POST /policies endpoint
        response = await api_client.post("/policies", json=payload)
        
        return {
            "success": True,
            "policy": response,
            "message": f"Policy '{policy_id}' created successfully"
        }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        print(f"[ERROR] Failed to create policy: {error_msg}")
        print(f"[ERROR] Payload was: {payload}")
        
        # Check for common error cases
        if "409" in error_msg or "already exists" in error_msg.lower():
            return {
                "success": False,
                "error": f"Policy '{policy_id}' already exists",
                "error_type": "ConflictError"
            }
        elif "404" in error_msg:
            return {
                "success": False,
                "error": "API endpoint not found",
                "error_type": "NotFoundError"
            }
        elif "422" in error_msg or "validation" in error_msg.lower():
            return {
                "success": False,
                "error": f"Validation error: {error_msg}",
                "error_type": "ValidationError",
                "payload": payload  # Include payload for debugging
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }


@mcp.tool()
async def delete_policy(
    policy_id: str,
    tenant_id: str,
    site_id: str
) -> Dict[str, Any]:
    """
    Delete an alert policy by ID.
    
    This tool calls the FastAPI endpoint: DELETE /policies/{policy_id}
    
    Validates that the policy belongs to the specified tenant/site before deletion.
    
    Args:
        policy_id: Unique policy identifier to delete (e.g., "POLICY_PPE_SITE_01_0001")
        tenant_id: Tenant identifier (required for validation)
        site_id: Site identifier (required for validation)
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - message: Success message (if successful)
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    try:
        # First, validate that the policy belongs to the specified tenant/site
        try:
            existing_policy = await api_client.get(f"/policies/{policy_id}")
            
            # Verify tenant_id matches
            if existing_policy.get("tenant_id") != tenant_id:
                return {
                    "success": False,
                    "error": f"Policy '{policy_id}' does not belong to tenant '{tenant_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify site_id matches
            if existing_policy.get("site_id") != site_id:
                return {
                    "success": False,
                    "error": f"Policy '{policy_id}' does not belong to site '{site_id}'",
                    "error_type": "ValidationError"
                }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Policy '{policy_id}' not found",
                    "error_type": "NotFoundError"
                }
            # Re-raise other errors to be caught by outer exception handler
            raise
        
        # Validation passed, proceed with deletion
        # Call the FastAPI DELETE /policies/{policy_id} endpoint
        success = await api_client.delete(f"/policies/{policy_id}")
        
        if success:
            return {
                "success": True,
                "message": f"Policy '{policy_id}' deleted successfully"
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
                "error": f"Policy '{policy_id}' not found",
                "error_type": "NotFoundError"
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }


@mcp.tool()
async def update_policy(
    policy_id: str,
    tenant_id: str,
    site_id: str,
    anomaly_type: Optional[str] = None,
    severity_levels: Optional[List[str]] = None,
    channels: Optional[List[str]] = None,
    person_ids: Optional[List[str]] = None,
    min_severity: Optional[str] = None,
    enabled: Optional[bool] = None,
    priority: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update an existing alert policy.
    
    This tool calls the FastAPI endpoint: PUT /policies/{policy_id}
    
    Args:
        policy_id: Unique policy identifier to update
        tenant_id: Tenant identifier (required for validation)
        site_id: Site identifier (required for validation)
        anomaly_type: Optional new anomaly type
        severity_levels: Optional new severity levels
        channels: Optional new channels
        person_ids: Optional new person IDs
        min_severity: Optional new minimum severity
        enabled: Optional new enabled status
        priority: Optional new priority
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - policy: Updated policy object (if successful)
            - message: Success message
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    try:
        # First, validate that the policy belongs to the specified tenant/site
        try:
            existing_policy = await api_client.get(f"/policies/{policy_id}")
            
            # Verify tenant_id matches
            if existing_policy.get("tenant_id") != tenant_id:
                return {
                    "success": False,
                    "error": f"Policy '{policy_id}' does not belong to tenant '{tenant_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify site_id matches
            if existing_policy.get("site_id") != site_id:
                return {
                    "success": False,
                    "error": f"Policy '{policy_id}' does not belong to site '{site_id}'",
                    "error_type": "ValidationError"
                }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Policy '{policy_id}' not found",
                    "error_type": "NotFoundError"
                }
            raise

        # Helper to extract lists from existing routes if needed
        existing_routes = existing_policy.get("routes", [])
        
        # 1. Resolve effective values for all fields
        eff_anomaly_type = anomaly_type if anomaly_type is not None else existing_policy.get("anomaly_type")
        eff_min_severity = min_severity if min_severity is not None else existing_policy.get("min_severity")
        eff_enabled = enabled if enabled is not None else existing_policy.get("enabled")
        eff_priority = priority if priority is not None else existing_policy.get("priority")
        
        # 2. Resolve routing components (Severities, Channels, PersonIDs)
        # If any is provided, use it. If not, extract from existing routes (assuming uniform).
        
        # Extract existing sets
        ex_severities = set()
        ex_channels = set()
        ex_person_ids = set()
        
        for r in existing_routes:
            if r.get("severity"): ex_severities.add(r.get("severity"))
            for ch in r.get("channels", []): ex_channels.add(ch)
            for t in r.get("targets", []): 
                if t.get("target_type") == "PERSON": ex_person_ids.add(t.get("value"))
        
        eff_severity_levels = severity_levels if severity_levels is not None else list(ex_severities)
        eff_channels = channels if channels is not None else list(ex_channels)
        eff_person_ids = person_ids if person_ids is not None else list(ex_person_ids)

        # 3. Build strictly formatted routes
        new_routes = []
        unique_severities = sorted(list(set(eff_severity_levels)))
        
        for severity in unique_severities:
            targets = [
                {"target_type": "PERSON", "value": pid}
                for pid in eff_person_ids
            ]
            new_routes.append({
                "severity": severity.upper().strip(),
                "targets": targets,
                "channels": [ch.upper().strip() for ch in eff_channels]
            })

        # 4. Construct clean payload matching UpdatePolicy schema
        # The 422 error indicates _id, tenant_id, and site_id are NOT allowed in the PUT body.
        clean_payload = {
            "anomaly_type": eff_anomaly_type.upper().strip() if eff_anomaly_type else "", 
            "min_severity": eff_min_severity.upper().strip() if eff_min_severity else "WARNING",
            "enabled": eff_enabled if eff_enabled is not None else True,
            "priority": eff_priority if eff_priority is not None else 100,
            "routes": new_routes
        }
        
        print(f"[DEBUG] Updating policy '{policy_id}' with CLEAN payload (v2): {clean_payload}")
        
        response = await api_client.put(f"/policies/{policy_id}", json=clean_payload)
        
        return {
            "success": True,
            "policy": response,
            "message": f"Policy '{policy_id}' updated successfully"
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Failed to update policy: {error_msg}")
        # Try to print response body if available (e.g. for 422 errors)
        if hasattr(e, "response") and e.response is not None:
             try:
                 print(f"[ERROR] Response body: {e.response.text}")
             except:
                 pass
                 
        return {
            "success": False,
            "error": error_msg,
            "error_type": type(e).__name__
        }
