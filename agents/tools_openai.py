# tools_openai.py

"""
Tool schemas for OpenAI function-calling integration.

Defines tools for PPE monitoring workflows and resource creation.
"""

configure_ppe_tool = {
    "type": "function",
    "function": {
        "name": "configure_ppe_workflow",
        "description": (
            "Enable PPE monitoring for cameras. You can filter by camera ID, location, or both. "
            "At least one of camera_id or location_filter must be provided. "
            "\n\nIMPORTANT: Do NOT confuse camera_id with gateway_id!"
            "\n- camera_id: Specific camera (e.g., 'CAM_GW_SITE_01_01', 'CAM_GATE3_001')"
            "\n- gateway_id: Gateway device (e.g., 'GW_SITE_01_0001') - usually from sticky defaults"
            "\n- location_filter: Physical location (e.g., 'Entry Gate', 'Gate 3')"
            "\n\nExamples:"
            "\n1. Enable for specific camera: camera_id='CAM_GW_SITE_01_01'"
            "\n2. Enable for location: location_filter='Entry Gate'"
            "\n3. Enable for camera at location: camera_id='CAM_GW_SITE_01_01', location_filter='Entry Gate'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier (optional - uses sticky default if not provided)"
                },
                "site_id": {
                    "type": "string",
                    "description": "Site identifier (optional - uses sticky default if not provided)"
                },
                "gateway_id": {
                    "type": "string",
                    "description": "Gateway identifier like 'GW_SITE_01_0001' (optional - uses sticky default). NOT a camera ID!"
                },
                "camera_id": {
                    "type": "string",
                    "description": "Specific camera ID like 'CAM_GW_SITE_01_01' or 'CAM_GATE3_001' (optional)"
                },
                "location_filter": {
                    "type": "string",
                    "description": (
                        "Physical location name like 'Entry Gate' or 'Gate 3' (optional). "
                        "All cameras at this location will have PPE monitoring enabled."
                    )
                }
            },
            "required": []
        },
    },
}

create_camera_tool = {
    "type": "function",
    "function": {
        "name": "create_camera_workflow",
        "description": "Create a new camera asset",
        "parameters": {
            "type": "object",
            "properties": {
                "camera_id": {"type": "string", "description": "Unique camera ID (e.g., CAM_GATE3_001)"},
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "gateway_id": {"type": "string", "description": "Gateway ID (optional - uses sticky default)"},
                "name": {"type": "string", "description": "Human-readable camera name"},
                "rtsp_url": {"type": "string", "description": "RTSP stream URL"},
                "onvif_url": {"type": "string", "description": "ONVIF URL"},
                "location": {"type": "string", "description": "Camera location (e.g., Gate 3)"},
                "userid": {"type": "string", "description": "Optional camera authentication username"},
                "password": {"type": "string", "description": "Optional camera authentication password"},
                "target_profile_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of detection profile IDs to assign to this camera"
                },
                "assigned_policy_id": {
                    "type": "string",
                    "description": "Optional alert policy ID to assign to this camera"
                },
            },
            "required": ["camera_id", "name", "rtsp_url", "onvif_url", "userid", "password"]
        }
    }
}

delete_camera_tool = {
    "type": "function",
    "function": {
        "name": "delete_camera_workflow",
        "description": "Delete a camera asset by ID. Requires tenant_id, site_id, and gateway_id for validation.",
        "parameters": {
            "type": "object",
            "properties": {
                "camera_id": {"type": "string", "description": "Unique camera ID to delete (e.g., CAM_GATE3_001)"},
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "gateway_id": {"type": "string", "description": "Gateway ID (optional - uses sticky default)"},
            },
            "required": ["camera_id"]
        }
    }
}

create_profile_tool = {
    "type": "function",
    "function": {
        "name": "create_profile_workflow",
        "description": "Create a new detection profile for object detection",
        "parameters": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string", "description": "Unique profile ID (e.g., PROFILE_PPE_001)"},
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "gateway_id": {"type": "string", "description": "Gateway ID (optional - uses sticky default)"},
                "name": {"type": "string", "description": "Profile name (e.g., PPE Detection)"},
                "targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Detection targets (e.g., ['helmet', 'vest', 'person'])"
                }
            },
            "required": ["profile_id", "name", "targets"]
        }
    }
}

create_policy_tool = {
    "type": "function",
    "function": {
        "name": "create_policy_workflow",
        "description": "Create a new alert policy for anomaly routing",
        "parameters": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "Unique policy ID (e.g., POLICY_PPE_SITE_01_0001)"},
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "anomaly_type": {"type": "string", "description": "Anomaly type (e.g., PPE_VIOLATION)"},
                "severity_levels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Severity levels to route (e.g., ['WARNING', 'CRITICAL'])"
                },
                "channels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Notification channels (e.g., ['EMAIL', 'SIP_PTT', 'HMI_POPUP'])"
                },
                "person_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Personnel IDs to notify"
                },
            },
            "required": ["policy_id", "anomaly_type", "severity_levels", "channels", "person_ids"]
        }
    }
}

create_personnel_tool = {
    "type": "function",
    "function": {
        "name": "create_personnel_workflow",
        "description": "Create a new personnel record for alert routing and notifications",
        "parameters": {
            "type": "object",
            "properties": {
                "person_id": {"type": "string", "description": "Unique personnel ID (e.g., P_SUPERVISOR_1)"},
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "name": {"type": "string", "description": "Person's full name"},
                "role": {"type": "string", "description": "Role/job title (e.g., supervisor, security, operator)"},
                "phone": {"type": "string", "description": "Optional phone number"},
                "email": {"type": "string", "description": "Optional email address"},
                "sip_uri": {"type": "string", "description": "Optional SIP URI for VoIP calls"},
                "on_call": {"type": "boolean", "description": "Whether person is currently on-call (default: false)"},
                "status": {"type": "string", "description": "Personnel status (default: ACTIVE)"},
            },
            "required": ["person_id", "name", "role"]
        }
    }
}

setup_ppe_site_tool = {
    "type": "function",
    "function": {
        "name": "setup_ppe_site_workflow",
        "description": "Complete PPE site setup - creates cameras, profiles, policies, and configures everything",
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "gateway_id": {"type": "string", "description": "Gateway ID (optional - uses sticky default)"},
                "cameras_config": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "camera_id": {"type": "string"},
                            "name": {"type": "string"},
                            "rtsp_url": {"type": "string"},
                            "onvif_url": {"type": "string"},
                            "location": {"type": "string"},
                        }
                    },
                    "description": "List of cameras to create"
                },
                "personnel_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Personnel IDs for alert routing"
                }
            },
            "required": ["cameras_config"]
        }
    }
}

disable_ppe_tool = {
    "type": "function",
    "function": {
        "name": "disable_ppe",
        "description": "Disable PPE monitoring for a specific camera. Sets camera status to INACTIVE and removes sensor data from legacy system.",
        "parameters": {
            "type": "object",
            "properties": {
                "camera_id": {"type": "string", "description": "Camera ID to disable PPE for (e.g., CAM_GATE3_001)"},
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "gateway_id": {"type": "string", "description": "Gateway ID (optional - uses sticky default)"}
            },
            "required": ["camera_id"]
        }
    }
}

# --- Query Tools ---

query_camera_full_context_tool = {
    "type": "function",
    "function": {
        "name": "query_camera_full_context",
        "description": (
            "Get complete context for a camera including all related resources. "
            "Returns camera details along with assigned model, profiles, policy, and personnel. "
            "Use this when you need comprehensive information about a camera's configuration."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "camera_id": {"type": "string", "description": "Camera ID to query (e.g., CAM_GATE3_001)"},
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "gateway_id": {"type": "string", "description": "Gateway ID (optional - uses sticky default)"}
            },
            "required": ["camera_id"]
        }
    }
}

query_site_health_tool = {
    "type": "function",
    "function": {
        "name": "query_site_health",
        "description": (
            "Analyze site health and get recommendations. "
            "Returns health score (0-100), camera status counts, lists of unconfigured cameras, "
            "and actionable recommendations for improving site configuration. "
            "Use this to check overall site status or identify configuration issues."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "gateway_id": {"type": "string", "description": "Gateway ID (optional - uses sticky default)"}
            },
            "required": []
        }
    }
}

query_ppe_status_tool = {
    "type": "function",
    "function": {
        "name": "query_ppe_configuration_status",
        "description": (
            "Check PPE configuration status for cameras. "
            "Categorizes cameras by configuration completeness: "
            "fully configured (has PPE model + profile + policy), "
            "partially configured (has some components), "
            "or not configured (no PPE components). "
            "Use this to check which cameras are ready for PPE monitoring."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "Tenant ID (optional - uses sticky default)"},
                "site_id": {"type": "string", "description": "Site ID (optional - uses sticky default)"},
                "gateway_id": {"type": "string", "description": "Gateway ID (optional - uses sticky default)"},
                "location_filter": {"type": "string", "description": "Optional location filter (e.g., 'Gate 3')"}
            },
            "required": []
        }
    }
}

query_sticky_defaults_tool = {
    "type": "function",
    "function": {
        "name": "query_sticky_defaults",
        "description": (
            "Get current sticky default values. "
            "Returns the current tenant_id, site_id, and gateway_id that will be used "
            "when not explicitly provided in requests. "
            "Use this to check what defaults are currently active."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

# Export all tools
ALL_TOOLS = [
    configure_ppe_tool,
    create_camera_tool,
    delete_camera_tool,
    create_profile_tool,
    create_policy_tool,
    create_personnel_tool,
    setup_ppe_site_tool,
    disable_ppe_tool,
    # Query tools
    query_camera_full_context_tool,
    query_site_health_tool,
    query_ppe_status_tool,
    query_sticky_defaults_tool,
]

