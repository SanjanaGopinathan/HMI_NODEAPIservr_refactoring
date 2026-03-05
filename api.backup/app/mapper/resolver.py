"""
Policy and Profile Resolver Service

Resolves alert_rule.subscribers[] and alert_rule.safety[] from asset bindings.
Implements strict error handling - raises HTTPException for missing data.
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from app.mapper.sensor import AlertSubscriber
import logging

logger = logging.getLogger(__name__)


# PPE target mapping (exact, case-insensitive)
PPE_TARGET_MAP = {
    "vest": "Safety Vest",
    "helmet": "Hardhat",
    "mask": "Mask"
}

# Deterministic safety label order
SAFETY_LABEL_ORDER = ["Hardhat", "Safety Vest", "Mask"]


async def resolve_policy_subscribers(
    policy_data: Dict[str, Any],
    personnel_data: List[Dict[str, Any]],
    asset: Dict[str, Any]
) -> List[AlertSubscriber]:
    """
    Resolve alert subscribers from policy PERSON targets.
    
    Args:
        policy_data: Complete policy document (from hmi_db.policies)
        personnel_data: List of complete personnel documents (from hmi_db.personnel)
        asset: Asset document (for logging context)
        
    Returns:
        List of AlertSubscriber objects with phone numbers
        
    Raises:
        HTTPException(400): Policy disabled or missing required fields
        HTTPException(404): Personnel not found for PERSON target
        HTTPException(400): Personnel missing contact.phone
    """
    asset_id = asset.get("_id", "UNKNOWN")
    tenant_id = asset.get("tenant_id", "UNKNOWN")
    site_id = asset.get("site_id", "UNKNOWN")
    gateway_id = asset.get("gateway_id", "UNKNOWN")
    policy_id = policy_data.get("_id", "UNKNOWN")
    
    log_context = {
        "asset_id": asset_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "policy_id": policy_id
    }
    
    logger.info(f"Resolving policy subscribers", extra=log_context)
    
    # Check if policy is enabled
    if not policy_data.get("enabled", False):
        logger.error(f"Policy is disabled: {policy_id}", extra=log_context)
        raise HTTPException(
            status_code=400,
            detail=f"Policy '{policy_id}' is disabled"
        )
    
    # Extract PERSON targets from routes
    person_targets = []
    routes = policy_data.get("routes", [])
    
    for route in routes:
        targets = route.get("targets", [])
        for target in targets:
            target_type = target.get("target_type")
            if target_type == "PERSON":
                person_id = target.get("value")
                if person_id:
                    person_targets.append(person_id)
    
    logger.info(
        f"Found {len(person_targets)} PERSON targets in policy",
        extra={**log_context, "person_count": len(person_targets)}
    )
    
    # Create a lookup map for personnel by ID
    personnel_map = {p.get("_id"): p for p in personnel_data}
    
    # Resolve each PERSON target to phone number
    subscribers = []
    seen_phones = set()
    
    for person_id in person_targets:
        # Lookup personnel from provided data
        personnel = personnel_map.get(person_id)
        if not personnel:
            logger.error(
                f"Personnel not found: {person_id}",
                extra={**log_context, "personnel_id": person_id}
            )
            raise HTTPException(
                status_code=404,
                detail=f"Personnel '{person_id}' not found in provided personnel_data"
            )
        
        # Extract phone number
        phone = personnel.get("contact", {}).get("phone")
        if not phone:
            logger.error(
                f"Personnel missing contact.phone: {person_id}",
                extra={**log_context, "personnel_id": person_id}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Personnel '{person_id}' missing required field: contact.phone"
            )
        
        # Deduplicate by phone number
        if phone not in seen_phones:
            seen_phones.add(phone)
            subscribers.append(AlertSubscriber(subscriber_id=phone))
            logger.debug(
                f"Resolved subscriber: {person_id} -> {phone}",
                extra={**log_context, "personnel_id": person_id, "phone": phone}
            )
    
    # Sort subscribers by phone for deterministic output
    subscribers.sort(key=lambda s: s.subscriber_id)
    
    logger.info(
        f"Resolved {len(subscribers)} unique subscribers",
        extra={**log_context, "subscriber_count": len(subscribers)}
    )
    
    return subscribers


async def resolve_profile_safety(
    profile_data: Dict[str, Any],
    asset: Dict[str, Any]
) -> List[str]:
    """
    Resolve safety labels from profile targets.
    
    Args:
        profile_data: Complete profile document (from hmi_db.profiles)
        asset: Asset document (for logging context)
        
    Returns:
        List of safety labels in deterministic order
        
    Raises:
        HTTPException(404): Profile not found
    """
    asset_id = asset.get("_id", "UNKNOWN")
    tenant_id = asset.get("tenant_id", "UNKNOWN")
    site_id = asset.get("site_id", "UNKNOWN")
    gateway_id = asset.get("gateway_id", "UNKNOWN")
    profile_id = profile_data.get("_id", "UNKNOWN")
    
    log_context = {
        "asset_id": asset_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "profile_id": profile_id
    }
    
    logger.info(f"Resolving profile safety labels", extra=log_context)
    
    # Extract and map targets
    targets = profile_data.get("targets", [])
    safety_labels = set()
    
    for target in targets:
        # Normalize: trim and lowercase
        normalized = target.strip().lower()
        
        # Map to safety label
        if normalized in PPE_TARGET_MAP:
            safety_label = PPE_TARGET_MAP[normalized]
            safety_labels.add(safety_label)
            logger.debug(
                f"Mapped target: {target} -> {safety_label}",
                extra={**log_context, "target": target, "label": safety_label}
            )
        else:
            logger.warning(
                f"Unknown PPE target, ignoring: {target}",
                extra={**log_context, "target": target}
            )
    
    # Sort by deterministic order
    sorted_labels = [
        label for label in SAFETY_LABEL_ORDER
        if label in safety_labels
    ]
    
    logger.info(
        f"Resolved {len(sorted_labels)} safety labels",
        extra={**log_context, "safety_count": len(sorted_labels), "labels": sorted_labels}
    )
    
    return sorted_labels
