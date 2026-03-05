from pydantic import BaseModel, Field


class SubscriberModel(BaseModel):
    """IOTA-E user-data subscriber model"""
    id: str = Field(alias="_id")  # Tel number (e.g., +301234567890)
    publicSipId: str  # sip:+301234567890@ecrio.com
    publicTelId: str  # tel:+301234567890
    imsDomain: str = "ecrio.com"
    privateId: str  # +301234567890@ecrio.com
    password: str = "ecrio@123"
    authMechanism: int = 1
    isBlocked: bool = False
    
    class Config:
        populate_by_name = True
