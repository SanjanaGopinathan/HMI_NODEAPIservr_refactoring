from typing import List
from pydantic import BaseModel, Field


class SensorDetails(BaseModel):
    """Sensor connection details"""
    ip: str
    port: int
    username: str
    password: str
    uuid: str
    onvif_url: str


class AlertSubscriber(BaseModel):
    """Alert subscriber configuration"""
    subscriber_id: str
    message_type: str = "VOICE"
    services: List[str] = ["MCPTT"]


class AlertRule(BaseModel):
    """Alert rule configuration"""
    alert_type: str = "videosur"
    safety: List[str] = []  # e.g., ["Hardhat", "Safety Vest"]
    subscribers: List[AlertSubscriber] = []


class SensorModel(BaseModel):
    """DT_ConfigStorage sensor model"""
    id: str = Field(alias="_id")
    sensor_id: str = "Camera"
    subscriber_id: str  # Primary subscriber tel number
    sensor_type: str = "CAMSNSR"
    camera_type: str = "onvif"
    name: str
    DOR: str  # Date of registration (MM-DD-YYYY)
    sensor_details: SensorDetails
    alert_rule: AlertRule
    description: str = ""
    unit: str = ""
    
    class Config:
        populate_by_name = True
