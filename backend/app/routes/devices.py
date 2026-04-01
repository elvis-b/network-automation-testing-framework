"""
Device Routes

CRUD operations for network device management.
"""

import logging
from datetime import datetime
from typing import List, Optional

from app.database.mongodb import get_database
from app.models.device import (
    DeviceCreate,
    DeviceListResponse,
    DeviceResponse,
    DeviceStatus,
    DeviceType,
    DeviceUpdate,
)
from app.routes.auth import get_current_user
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
router = APIRouter()


def device_helper(device: dict) -> dict:
    """Convert MongoDB document to response format."""
    return {
        "id": str(device["_id"]),
        "name": device["name"],
        "ip_address": device["ip_address"],
        "device_type": device["device_type"],
        "vendor": device.get("vendor"),
        "model": device.get("model"),
        "status": device["status"],
        "location": device.get("location"),
        "created_at": device["created_at"],
        "updated_at": device["updated_at"],
        "last_seen": device.get("last_seen"),
        "metadata": device.get("metadata"),
    }


@router.get("", response_model=DeviceListResponse)
async def get_devices(
    status: Optional[DeviceStatus] = Query(None, description="Filter by status"),
    device_type: Optional[DeviceType] = Query(
        None, alias="type", description="Filter by device type"
    ),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of all devices with optional filtering.

    Args:
        status: Filter by device status
        device_type: Filter by device type
        search: Search term for device name
        limit: Maximum results to return
        offset: Pagination offset

    Returns:
        List of devices with pagination info
    """
    logger.info(f"Getting devices - user: {current_user.get('sub')}")

    db = get_database()
    devices_collection = db["devices"]

    # Build query
    query = {}

    if status:
        query["status"] = status.value

    if device_type:
        query["device_type"] = device_type.value

    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    # Get total count
    total = await devices_collection.count_documents(query)

    # Get devices with pagination
    cursor = devices_collection.find(query).skip(offset).limit(limit).sort("name", 1)
    devices = await cursor.to_list(length=limit)

    device_list = [DeviceResponse(**device_helper(device)) for device in devices]

    return DeviceListResponse(
        devices=device_list, total=total, limit=limit, offset=offset
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get a specific device by ID.

    Args:
        device_id: Device unique identifier

    Returns:
        Device details

    Raises:
        HTTPException: If device not found
    """
    logger.info(f"Getting device {device_id} - user: {current_user.get('sub')}")

    try:
        object_id = ObjectId(device_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid device ID format"
        )

    db = get_database()
    devices_collection = db["devices"]

    device = await devices_collection.find_one({"_id": object_id})

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    return DeviceResponse(**device_helper(device))


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate, current_user: dict = Depends(get_current_user)
):
    """
    Create a new device.

    Args:
        device: Device data

    Returns:
        Created device

    Raises:
        HTTPException: If device name already exists
    """
    logger.info(f"Creating device {device.name} - user: {current_user.get('sub')}")

    db = get_database()
    devices_collection = db["devices"]

    # Check for duplicate name
    existing = await devices_collection.find_one({"name": device.name})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device with this name already exists",
        )

    # Check for duplicate IP
    existing_ip = await devices_collection.find_one({"ip_address": device.ip_address})
    if existing_ip:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device with this IP address already exists",
        )

    # Create device document
    now = datetime.utcnow()
    device_doc = {
        **device.model_dump(),
        "created_at": now,
        "updated_at": now,
        "last_seen": None,
    }

    result = await devices_collection.insert_one(device_doc)

    # Fetch created device
    created_device = await devices_collection.find_one({"_id": result.inserted_id})

    logger.info(f"Device created: {device.name} (ID: {result.inserted_id})")

    return DeviceResponse(**device_helper(created_device))


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update an existing device.

    Args:
        device_id: Device unique identifier
        device_update: Fields to update

    Returns:
        Updated device

    Raises:
        HTTPException: If device not found
    """
    logger.info(f"Updating device {device_id} - user: {current_user.get('sub')}")

    try:
        object_id = ObjectId(device_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid device ID format"
        )

    db = get_database()
    devices_collection = db["devices"]

    # Check device exists
    existing = await devices_collection.find_one({"_id": object_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Build update data (only non-None fields)
    update_data = {k: v for k, v in device_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields to update"
        )

    # Check for duplicate name if name is being updated
    if "name" in update_data and update_data["name"] != existing["name"]:
        name_exists = await devices_collection.find_one(
            {"name": update_data["name"], "_id": {"$ne": object_id}}
        )
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device with this name already exists",
            )

    # Check for duplicate IP if IP is being updated
    if (
        "ip_address" in update_data
        and update_data["ip_address"] != existing["ip_address"]
    ):
        ip_exists = await devices_collection.find_one(
            {"ip_address": update_data["ip_address"], "_id": {"$ne": object_id}}
        )
        if ip_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device with this IP address already exists",
            )

    update_data["updated_at"] = datetime.utcnow()

    await devices_collection.update_one({"_id": object_id}, {"$set": update_data})

    # Fetch updated device
    updated_device = await devices_collection.find_one({"_id": object_id})

    logger.info(f"Device updated: {device_id}")

    return DeviceResponse(**device_helper(updated_device))


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a device.

    Args:
        device_id: Device unique identifier

    Raises:
        HTTPException: If device not found
    """
    logger.info(f"Deleting device {device_id} - user: {current_user.get('sub')}")

    try:
        object_id = ObjectId(device_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid device ID format"
        )

    db = get_database()
    devices_collection = db["devices"]

    # Check device exists
    existing = await devices_collection.find_one({"_id": object_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Delete device
    await devices_collection.delete_one({"_id": object_id})

    # Also delete associated alerts
    alerts_collection = db["alerts"]
    await alerts_collection.delete_many({"device_id": device_id})

    logger.info(f"Device deleted: {device_id}")

    return None
