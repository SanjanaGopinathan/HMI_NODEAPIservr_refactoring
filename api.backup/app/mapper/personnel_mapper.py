import random
from typing import Dict, Any, Optional
from app.mapper.subscriber import SubscriberModel
from app.config import settings


class PersonnelToSubscriberMapper:
    """Maps HMI personnel to IOTA-E subscriber format"""
    
    @staticmethod
    def generate_tel_number() -> str:
        """Generate random tel number with prefix +3012345XXXXX"""
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(5)])
        return f"{settings.SUBSCRIBER_TEL_PREFIX}{random_digits}"
    
    @staticmethod
    def map_personnel_to_subscriber(
        personnel: Dict[str, Any],
        tel_number: Optional[str] = None
    ) -> SubscriberModel:
        """Transform HMI personnel to IOTA-E subscriber
        
        Args:
            personnel: HMI personnel document from hmi/personnel collection
            tel_number: Optional tel number, if not provided will be generated
            
        Returns:
            SubscriberModel ready for upsert to iota-e/user-data
        """
        
        # Generate or use provided tel number
        if not tel_number:
            tel_number = PersonnelToSubscriberMapper.generate_tel_number()
        
        # Build subscriber model
        subscriber = SubscriberModel(
            _id=tel_number,
            publicSipId=f"sip:{tel_number}@{settings.IMSI_DOMAIN}",
            publicTelId=f"tel:{tel_number}",
            imsDomain=settings.IMSI_DOMAIN,
            privateId=f"{tel_number}@{settings.IMSI_DOMAIN}",
            password=settings.DEFAULT_PASSWORD,
            authMechanism=1,
            isBlocked=False
        )
        
        return subscriber
