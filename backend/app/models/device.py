"""
Device Models

Pydantic models for network device data validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import re


class DeviceType(str, Enum):
    """Device type enumeration."""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"


class DeviceStatus(str, Enum):
    """Device status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class DeviceBase(BaseModel):
    """Base device model with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    ip_address: str = Field(..., description="IPv4 address")
    device_type: DeviceType
    vendor: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    status: DeviceStatus = DeviceStatus.ACTIVE
    location: Optional[str] = Field(None, max_length=200)
    
    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """Validate IPv4 address format."""
        pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if not re.match(pattern, v):
            raise ValueError("Invalid IPv4 address format")
        return v


class DeviceCreate(DeviceBase):
    """Model for creating a new device."""
    metadata: Optional[Dict[str, Any]] = None


class DeviceUpdate(BaseModel):
    """Model for updating a device."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    ip_address: Optional[str] = None
    device_type: Optional[DeviceType] = None
    vendor: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    status: Optional[DeviceStatus] = None
    location: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate IPv4 address format if provided."""
        if v is None:
            return v
        pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if not re.match(pattern, v):
            raise ValueError("Invalid IPv4 address format")
        return v


class DeviceInDB(DeviceBase):
    """Device model as stored in database."""
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime
    last_seen: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class DeviceResponse(DeviceBase):
    """Device model for API responses."""
    id: str
    created_at: datetime
    updated_at: datetime
    last_seen: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class Device(DeviceBase):
    """Full device model."""
    id: str
    created_at: datetime
    updated_at: datetime
    last_seen: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceListResponse(BaseModel):
    """Response model for device list endpoint."""
    devices: List[DeviceResponse]
    total: int
    limit: int
    offset: int

