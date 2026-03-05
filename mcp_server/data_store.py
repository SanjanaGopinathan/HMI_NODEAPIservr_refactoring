# mcp_server/data_store.py
"""
In-memory canned data for testing the MCP server end-to-end.

NOTE:
- This data lives in process memory only.
- It resets every time the MCP server restarts.
"""

from __future__ import annotations
from typing import List, Dict, Any

TENANT_ID = "TENANT_01"
SITE_ID = "SITE_01"
GATEWAY_ID_01 = "GTW01"
GATEWAY_ID_02 = "GTW02"

# --- Assets as Sensor/Camera ---

MOCK_ASSETS: List[Dict[str, Any]] = [
    {
        "_id": "CAM_GATE3_001",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "gateway_id": GATEWAY_ID_01,  
        "name": "Gate 3 Camera 001",
        "location": "Gate 3",
        "zone": "ENTRY",
        "status": "INACTIVE",
        "asset_info":{
            "type": "CAMERA",
            "capabilities": ["VIDEO_STREAM", "OBJECT_DETECTION"],
            "camera": {
                "stream": {
                "rtsp_url": "rtsp://user:pass@10.0.0.10/stream1",
                "onvif_url": "http://10.0.0.10:8000",		  
                "fps": 10
                },
                "resolution": "1920x1080",
                "userid": "admin",
                "password": "camera123"
            },
            "bindings": {
                "assigned_model_id": "MODEL_PPE_YOLOV12",
                "target_profile_ids": ["PROFILE_PPE_001"],
                "assigned_policy_id": "POLICY_PPE_SITE_01_0001"
            },
            "tags": ["gate", "ppe"]
        },
        "created_at": "2025-12-01T00:00:00Z",
        "updated_at": "2025-12-15T05:40:00Z"
    },
    {
        "_id": "CAM_GATE4_002",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "gateway_id": GATEWAY_ID_02,  
        "name": "Gate 4 Camera 002",
        "location": "Gate 4",
        "zone": "ENTRY",
        "status": "INACTIVE",
        "asset_info":{
            "type": "CAMERA",
            "capabilities": ["VIDEO_STREAM", "OBJECT_DETECTION"],
            "camera": {
                "stream": {
                "rtsp_url": "rtsp://user:pass@10.0.0.11/stream1",
                "onvif_url": "http://10.0.0.11:8000",		  
                "fps": 10
                },
                "resolution": "1920x1080",
                "userid": "admin",
                "password": "camera456"
            },
            "bindings": {
                "assigned_model_id": "MODEL_INTRUSION_V1",
                "target_profile_ids": ["PROFILE_INTRUSION_001"],
                "assigned_policy_id": "POLICY_INTR_SITE_01_0001"
            },
            "tags": ["restricted", "intrusion"]
        },
        "created_at": "2025-12-01T00:00:00Z",
        "updated_at": "2025-12-15T05:40:00Z"
    },
    {
        "_id": "CAM_GATE5_003",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "gateway_id": GATEWAY_ID_02,  
        "name": "Gate 5 Camera 003",
        "location": "Gate 5",
        "zone": "ENTRY",
        "status": "ACTIVE",
        "asset_info":{
            "type": "CAMERA",
            "capabilities": ["VIDEO_STREAM", "OBJECT_DETECTION"],
            "camera": {
                "stream": {
                "rtsp_url": "rtsp://user:pass@10.0.0.11/stream1",
                "onvif_url": "http://10.0.0.11:8000",		  
                "fps": 10
                },
                "resolution": "1920x1080",
                "userid": "admin",
                "password": "camera789"
            },
            "bindings": {
                "assigned_model_id": "MODEL_INTRUSION_V1",
                "target_profile_ids": ["PROFILE_INTRUSION_001"],
                "assigned_policy_id": "POLICY_INTR_SITE_01_0001"
            },
            "tags": ["restricted", "intrusion"]
        },
        "created_at": "2025-12-01T00:00:00Z",
        "updated_at": "2025-12-15T05:40:00Z"
    }
]

# --- Detection Profiles ---

MOCK_DETECTION_PROFILES: List[Dict[str, Any]] = [
    {
        "_id": "PROFILE_PPE_001",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "name": "PPE Detection",
        "targets": ["helmet", "vest"],
    },
    {
        "_id": "PROFILE_INTRUSION_001",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "name": "Intrusion Detection",
        "targets": ["person", "vehicle"],
    },
]

# --- Models ---

MOCK_MODELS: List[Dict[str, Any]] = [
    {
        "_id": "MODEL_PPE_YOLOV12",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "gateway_id": GATEWAY_ID_01,
        "name": "PPE-Detector-YOLOv12",
        "framework_id": "openvino-2024.1",
        "status": "ACTIVE",
    },
    {
        "_id": "MODEL_INTRUSION_V1",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "gateway_id": GATEWAY_ID_02,
        "name": "Intrusion-Detector-V1",
        "framework_id": "openvino-2024.1",
        "status": "ACTIVE",
    },
]

# --- Personnel ---

MOCK_PERSONNEL: List[Dict[str, Any]] = [
    {
        "_id": "P_SUPERVISOR_1",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "name": "Shift Supervisor A",
        "role": "supervisor",
        "contact": {
            "phone": "+91-90000-00001",
            "email": "supervisorA@tenant.example",
            "sip_uri": "sip:supervisorA@example.com"
        },
        "on_call": False,
        "status": "ACTIVE",
        "created_at": "2025-12-01T00:00:00Z",
        "updated_at": "2025-12-15T05:40:00Z"
    },
    {
        "_id": "P_SUPERVISOR_2",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "name": "Shift Supervisor B",
        "role": "supervisor",
        "contact": {
            "phone": "+91-90000-00002",
            "email": "supervisorB@tenant.example",
            "sip_uri": "sip:supervisorB@example.com"
        },
        "on_call": True,
        "status": "ACTIVE",
        "created_at": "2025-12-01T00:00:00Z",
        "updated_at": "2025-12-15T05:40:00Z"
    },
    {
        "_id": "P_WORKER_01",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "name": "Shift Worker A",
        "role": "worker",
        "contact": {
            "phone": "+91-91000-00001",
            "email": "workerA@tenant.example",
            "sip_uri": "sip:workerA@example.com"
        },
        "on_call": False,
        "status": "ACTIVE",
        "created_at": "2025-12-01T00:00:00Z",
        "updated_at": "2025-12-15T05:40:00Z"
    }
]

# --- Alert Policies (will be populated by set_alert_policy) ---

MOCK_ALERT_POLICIES: List[Dict[str, Any]] = [
    {
        "_id": "POLICY_PPE_SITE_01_0001",
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,
        "anomaly_type": "PPE_VIOLATION",
        "min_severity": "WARNING",
        "enabled": True,
        "priority": 100,
        "routes": [
            {
            "severity": "CRITICAL",
            "targets": [
                { "target_type": "ROLE", "value": "supervisor" },
                { "target_type": "PERSON", "value": "P_SUPERVISOR_1" }
            ],
            "channels": ["HMI_POPUP", "EMAIL", "PHONE_CALL", "SIP_PTT"]
            }
        ],
        "created_at": "2025-12-01T00:00:00Z",
        "updated_at": "2025-12-15T05:40:00Z"
    }
]

# --- Common severity ordering for alerts ---

SEVERITY_ORDER = ["INFO", "WARNING", "MAJOR", "CRITICAL"]


def severity_gte(a: str, b: str) -> bool:
    """Return True if severity a >= b using SEVERITY_ORDER."""
    try:
        return SEVERITY_ORDER.index(a.upper()) >= SEVERITY_ORDER.index(b.upper())
    except ValueError:
        return False
