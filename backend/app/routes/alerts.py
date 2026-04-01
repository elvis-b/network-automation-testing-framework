"""
Alert Routes

Manage network alerts and acknowledgments.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import logging

from app.database.mongodb import get_database
from app.models.alert import (
    AlertCreate, AlertResponse, AlertListResponse,
    AlertSeverity, AlertType, AcknowledgeResponse
)
from app.routes.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def alert_helper(alert: dict) -> dict:
    """Convert MongoDB document to response format."""
    return {
        "id": str(alert["_id"]),
        "device_id": alert["device_id"],
        "device_name": alert["device_name"],
        "severity": alert["severity"],
        "type": alert["type"],
        "message": alert["message"],
        "timestamp": alert["timestamp"],
        "acknowledged": alert.get("acknowledged", False),
        "acknowledged_by": alert.get("acknowledged_by"),
        "acknowledged_at": alert.get("acknowledged_at"),
        "resolved": alert.get("resolved", False),
        "resolved_at": alert.get("resolved_at")
    }


@router.get("", response_model=AlertListResponse)
async def get_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    alert_type: Optional[AlertType] = Query(None, alias="type", description="Filter by type"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of all alerts with optional filtering.
    
    Args:
        severity: Filter by alert severity
        alert_type: Filter by alert type
        acknowledged: Filter by acknowledgment status
        device_id: Filter by device
        
    Returns:
        List of alerts
    """
    logger.info(f"Getting alerts - user: {current_user.get('sub')}")
    
    db = get_database()
    alerts_collection = db["alerts"]
    
    # Build query
    query = {}
    
    if severity:
        query["severity"] = severity.value
    
    if alert_type:
        query["type"] = alert_type.value
    
    if acknowledged is not None:
        query["acknowledged"] = acknowledged
    
    if device_id:
        query["device_id"] = device_id
    
    # Get total count
    total = await alerts_collection.count_documents(query)
    
    # Get alerts sorted by timestamp (newest first) and severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    cursor = alerts_collection.find(query).sort([
        ("acknowledged", 1),  # Unacknowledged first
        ("timestamp", -1)     # Newest first
    ])
    
    alerts = await cursor.to_list(length=100)
    
    # Sort by severity within results
    alerts.sort(key=lambda x: (
        x.get("acknowledged", False),
        severity_order.get(x.get("severity", "info"), 2),
        -x.get("timestamp", datetime.min).timestamp()
    ))
    
    alert_list = [AlertResponse(**alert_helper(alert)) for alert in alerts]
    
    return AlertListResponse(
        alerts=alert_list,
        total=total
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific alert by ID.
    
    Args:
        alert_id: Alert unique identifier
        
    Returns:
        Alert details
        
    Raises:
        HTTPException: If alert not found
    """
    logger.info(f"Getting alert {alert_id} - user: {current_user.get('sub')}")
    
    try:
        object_id = ObjectId(alert_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID format"
        )
    
    db = get_database()
    alerts_collection = db["alerts"]
    
    alert = await alerts_collection.find_one({"_id": object_id})
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return AlertResponse(**alert_helper(alert))


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert: AlertCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new alert.
    
    Args:
        alert: Alert data
        
    Returns:
        Created alert
    """
    logger.info(f"Creating alert for device {alert.device_id} - user: {current_user.get('sub')}")
    
    db = get_database()
    alerts_collection = db["alerts"]
    
    # Create alert document
    alert_doc = {
        **alert.model_dump(),
        "timestamp": datetime.utcnow(),
        "acknowledged": False,
        "acknowledged_by": None,
        "acknowledged_at": None,
        "resolved": False,
        "resolved_at": None
    }
    
    result = await alerts_collection.insert_one(alert_doc)
    
    # Fetch created alert
    created_alert = await alerts_collection.find_one({"_id": result.inserted_id})
    
    logger.info(f"Alert created: {result.inserted_id}")
    
    return AlertResponse(**alert_helper(created_alert))


@router.put("/{alert_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Acknowledge an alert.
    
    Args:
        alert_id: Alert unique identifier
        
    Returns:
        Acknowledgment confirmation
        
    Raises:
        HTTPException: If alert not found or already acknowledged
    """
    username = current_user.get("sub")
    logger.info(f"Acknowledging alert {alert_id} - user: {username}")
    
    try:
        object_id = ObjectId(alert_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID format"
        )
    
    db = get_database()
    alerts_collection = db["alerts"]
    
    # Check alert exists
    alert = await alerts_collection.find_one({"_id": object_id})
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Check if already acknowledged
    if alert.get("acknowledged"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already acknowledged"
        )
    
    # Update alert
    now = datetime.utcnow()
    await alerts_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "acknowledged": True,
                "acknowledged_by": username,
                "acknowledged_at": now
            }
        }
    )
    
    logger.info(f"Alert acknowledged: {alert_id} by {username}")
    
    return AcknowledgeResponse(
        id=alert_id,
        acknowledged=True,
        acknowledged_by=username,
        acknowledged_at=now
    )


@router.put("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Resolve an alert.
    
    Args:
        alert_id: Alert unique identifier
        
    Returns:
        Resolved alert
        
    Raises:
        HTTPException: If alert not found or already resolved
    """
    username = current_user.get("sub")
    logger.info(f"Resolving alert {alert_id} - user: {username}")
    
    try:
        object_id = ObjectId(alert_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID format"
        )
    
    db = get_database()
    alerts_collection = db["alerts"]
    
    # Check alert exists
    alert = await alerts_collection.find_one({"_id": object_id})
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Check if already resolved
    if alert.get("resolved"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already resolved"
        )
    
    # Update alert - also acknowledge if not already
    now = datetime.utcnow()
    update_data = {
        "resolved": True,
        "resolved_at": now
    }
    
    if not alert.get("acknowledged"):
        update_data["acknowledged"] = True
        update_data["acknowledged_by"] = username
        update_data["acknowledged_at"] = now
    
    await alerts_collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
    )
    
    # Fetch updated alert
    updated_alert = await alerts_collection.find_one({"_id": object_id})
    
    logger.info(f"Alert resolved: {alert_id} by {username}")
    
    return AlertResponse(**alert_helper(updated_alert))


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an alert.
    
    Args:
        alert_id: Alert unique identifier
        
    Raises:
        HTTPException: If alert not found
    """
    logger.info(f"Deleting alert {alert_id} - user: {current_user.get('sub')}")
    
    try:
        object_id = ObjectId(alert_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID format"
        )
    
    db = get_database()
    alerts_collection = db["alerts"]
    
    # Check alert exists
    existing = await alerts_collection.find_one({"_id": object_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Delete alert
    await alerts_collection.delete_one({"_id": object_id})
    
    logger.info(f"Alert deleted: {alert_id}")
    
    return None

