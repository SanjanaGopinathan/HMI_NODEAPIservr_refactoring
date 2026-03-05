"""
Payload Transformation Utilities

Transform internal HMI Mapper models to Edge AI API payload format.
"""

from datetime import datetime
from typing import Dict, Any
from app.mapper.subscriber import SubscriberModel
from app.mapper.sensor import SensorModel
from app.config import settings


def subscriber_to_edge_ai_payload(
    subscriber_id: str,
    user_name: str = "User",
    password: str = None
) -> Dict[str, Any]:
    """
    Create Edge AI API add_subscriber payload
    
    Args:
        subscriber_id: Subscriber ID (phone number)
        user_name: Display name for user
        password: Password (defaults to settings.DEFAULT_PASSWORD)
        
    Returns:
        Edge AI API compatible payload
    """
    return {
        "subscriberId": subscriber_id,
        "password": password or settings.DEFAULT_PASSWORD,
        "userInfo": {
            "userName": user_name,
            "dor": datetime.now().strftime("%d-%m-%Y"),
            "org": settings.IMSI_DOMAIN
        },
        "service": {
            "comms": [{"isBlocked": False}]
        }
    }


def sensor_to_edge_ai_payload(sensor: SensorModel) -> Dict[str, Any]:
    """
    Transform SensorModel to Edge AI API add_sensor payload
    
    Args:
        sensor: Internal sensor model
        
    Returns:
        Edge AI API compatible payload (sensor dict with aliases)
    """
    return sensor.dict(by_alias=True)
