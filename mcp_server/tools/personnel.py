# mcp_server/tools/personnel.py
"""
Personnel management tools using FastAPI backend
"""
from typing import Dict, Any, Optional
from mcp_server.server import mcp
from mcp_server.api_client import api_client


@mcp.tool()
async def list_personnel(
    tenant_id: str,
    site_id: Optional[str] = None,
    role: Optional[str] = None,
    on_call: Optional[bool] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List personnel for a tenant with optional filtering.
    
    This tool calls the FastAPI endpoint: GET /personnel
    
    Args:
        tenant_id: Tenant identifier (required)
        site_id: Optional site filter
        role: Optional role filter (e.g., "supervisor", "security")
        on_call: Optional filter for on-call status
        status: Optional status filter (e.g., "ACTIVE", "INACTIVE")
    
    Returns:
        Dict containing:
            - personnel: List of personnel objects
            - count: Total number of personnel
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    # Build query parameters for the FastAPI endpoint
    params = {
        "tenant_id": tenant_id,
        "limit": 200,  # Get all personnel
        "offset": 0,
    }
    
    # Add optional filters
    if site_id is not None:
        params["site_id"] = site_id
    
    if role is not None:
        params["role"] = role
    
    if on_call is not None:
        params["on_call"] = on_call
    
    if status is not None:
        params["status"] = status
    
    try:
        # Call the FastAPI GET /personnel endpoint
        response = await api_client.get("/personnel", params=params)
        
        # Extract items from the response
        personnel = response.get("items", [])
        total = response.get("total", 0)
        
        # Return in the expected format
        return {
            "personnel": personnel,
            "count": total
        }
    
    except Exception as e:
        # Return error information in a structured way
        return {
            "personnel": [],
            "count": 0,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@mcp.tool()
async def create_personnel(
    person_id: str,
    tenant_id: str,
    site_id: str,
    name: str,
    role: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    sip_uri: Optional[str] = None,
    on_call: bool = False,
    status: str = "ACTIVE",
) -> Dict[str, Any]:
    """
    Create a new personnel record.
    
    This tool:
    1. Calls the FastAPI endpoint: POST /personnel to create the personnel record
    2. If phone number is provided, calls HMI Mapper: POST /api/create-subscriber
       to create a subscriber in iota-e/user-data for alert routing
    
    Args:
        person_id: Unique personnel identifier (e.g., "P_SUPERVISOR_1")
        tenant_id: Tenant identifier
        site_id: Site identifier
        name: Person's full name
        role: Role/job title (e.g., "supervisor", "security", "operator")
        phone: Optional phone number (required for subscriber creation)
        email: Optional email address
        sip_uri: Optional SIP URI for VoIP calls
        on_call: Whether person is currently on-call (default: False)
        status: Personnel status (default: "ACTIVE")
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - personnel: Created personnel object (if successful)
            - subscriber_id: Created subscriber ID (if phone provided and successful)
            - subscriber_error: Error message from subscriber creation (if failed)
            - message: Success message
            - error: Error message (if personnel creation failed)
            - error_type: Exception type (if failed)
    """
    
    # Build contact info
    contact = {}
    if phone is not None:
        contact["phone"] = phone
    if email is not None:
        contact["email"] = email
    if sip_uri is not None:
        contact["sip_uri"] = sip_uri
    
    # Build the personnel payload according to the PersonnelCreate schema
    payload = {
        "_id": person_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "name": name,
        "role": role,
        "contact": contact,
        "on_call": on_call,
        "status": status,
    }
    
    try:
        # Call the FastAPI POST /personnel endpoint
        response = await api_client.post("/personnel", json=payload)
        
        # After successfully creating personnel, create subscriber in legacy system
        # This is needed for alert routing in the iota-e system
        subscriber_id = None
        subscriber_error = None
        
        if phone:  # Only create subscriber if phone number is provided
            try:
                from mcp_server.hmi_mapper_client import hmi_mapper_client
                
                # Fetch the created personnel document to pass to HMI Mapper
                personnel_data = response  # The response contains the created personnel
                
                # Call HMI Mapper to create subscriber
                subscriber_result = await hmi_mapper_client.create_subscriber(personnel_data)
                
                if subscriber_result.get("success"):
                    subscriber_id = subscriber_result.get("subscriber_id")
                    print(f"? Created subscriber for personnel '{person_id}': {subscriber_id}")
                else:
                    subscriber_error = subscriber_result.get("error", "Unknown error")
                    print(f"? Failed to create subscriber: {subscriber_error}")
                    
            except Exception as e:
                subscriber_error = str(e)
                print(f"? Failed to create subscriber for personnel '{person_id}': {subscriber_error}")
        
        return {
            "success": True,
            "personnel": response,
            "subscriber_id": subscriber_id,
            "subscriber_error": subscriber_error,
            "message": f"Personnel '{person_id}' created successfully" + 
                      (f" with subscriber {subscriber_id}" if subscriber_id else "")
        }
    
    except Exception as e:
        # Return error information in a structured way
        error_msg = str(e)
        
        # Check for common error cases
        if "409" in error_msg or "already exists" in error_msg.lower():
            return {
                "success": False,
                "error": f"Personnel '{person_id}' already exists",
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
async def delete_personnel(
    person_id: str,
    tenant_id: str,
    site_id: str
) -> Dict[str, Any]:
    """
    Delete a personnel record by ID.
    
    This tool:
    1. Validates that the personnel belongs to the specified tenant/site
    2. Calls the FastAPI endpoint: DELETE /personnel/{person_id}
    3. Calls HMI Mapper: POST /api/delete-subscriber to clean up legacy subscriber
    
    Args:
        person_id: Unique personnel identifier to delete (e.g., "PERSON_SUPERVISOR_001")
        tenant_id: Tenant identifier (required for validation)
        site_id: Site identifier (required for validation)
    
    Returns:
        Dict containing:
            - success: Boolean indicating success
            - subscriber_deleted: Boolean indicating if subscriber was deleted
            - message: Success message (if successful)
            - error: Error message (if failed)
            - error_type: Exception type (if failed)
    """
    
    try:
        # First, validate that the personnel belongs to the specified tenant/site
        try:
            existing_personnel = await api_client.get(f"/personnel/{person_id}")
            
            # Verify tenant_id matches
            if existing_personnel.get("tenant_id") != tenant_id:
                return {
                    "success": False,
                    "error": f"Personnel '{person_id}' does not belong to tenant '{tenant_id}'",
                    "error_type": "ValidationError"
                }
            
            # Verify site_id matches
            if existing_personnel.get("site_id") != site_id:
                return {
                    "success": False,
                    "error": f"Personnel '{person_id}' does not belong to site '{site_id}'",
                    "error_type": "ValidationError"
                }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Personnel '{person_id}' not found",
                    "error_type": "NotFoundError"
                }
            # Re-raise other errors to be caught by outer exception handler
            raise
        
        # Validation passed, proceed with deletion
        # Before deleting personnel, try to delete their subscriber from legacy system
        subscriber_deleted = False
        subscriber_id = None
        subscriber_error = None
        
        try:
            from mcp_server.hmi_mapper_client import hmi_mapper_client
            
            # Fetch personnel data first before deleting
            personnel_data = await api_client.get(f"/personnel/{person_id}")
            
            if personnel_data:
                # Call HMI Mapper to delete subscriber
                subscriber_result = await hmi_mapper_client.delete_subscriber(personnel_data)
                
                if subscriber_result.get("success"):
                    subscriber_deleted = True
                    subscriber_id = subscriber_result.get("subscriber_id")
                    print(f"? Deleted subscriber for personnel '{person_id}': {subscriber_id}")
                else:
                    subscriber_error = subscriber_result.get("error", "Unknown error")
                    print(f"? Failed to delete subscriber: {subscriber_error}")
            else:
                print(f"? Personnel '{person_id}' not found, skipping subscriber deletion")
                
        except Exception as e:
            subscriber_error = str(e)
            print(f"? Failed to delete subscriber for personnel '{person_id}': {subscriber_error}")
        
        # Now delete the personnel record
        # Call the FastAPI DELETE /personnel/{person_id} endpoint
        success = await api_client.delete(f"/personnel/{person_id}")
        
        if success:
            return {
                "success": True,
                "subscriber_deleted": subscriber_deleted,
                "subscriber_id": subscriber_id,
                "message": f"Personnel '{person_id}' deleted successfully" +
                          (f" (subscriber {subscriber_id} also deleted)" if subscriber_deleted else "")
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
                "error": f"Personnel '{person_id}' not found",
                "error_type": "NotFoundError"
            }
        else:
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }
