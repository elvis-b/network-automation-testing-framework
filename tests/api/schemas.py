from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum
import re


class DeviceStatus(str, Enum):
    """Valid device status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class DeviceType(str, Enum):
    """Valid device type values."""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    ACCESS_POINT = "access_point"
    SERVER = "server"


class AlertSeverity(str, Enum):
    """Valid alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class DeviceResponse(BaseModel):
    """
    Schema for device API response.
    
    Validates that device responses contain required fields
    with correct types and constraints.
    """
    id: str = Field(..., min_length=1, description="Unique device identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Device name")
    ip_address: str = Field(..., description="Device IP address")
    status: str = Field(..., description="Device operational status")
    device_type: str = Field(..., description="Type of network device")
    vendor: Optional[str] = Field(None, description="Device vendor/manufacturer")
    model: Optional[str] = Field(None, description="Device model")
    location: Optional[str] = Field(None, description="Physical location")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    last_seen: Optional[str] = Field(None, description="Last seen timestamp")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """Validate IP address format."""
        parts = v.split('.')
        if len(parts) == 4:
            try:
                if all(0 <= int(part) <= 255 for part in parts):
                    return v
            except ValueError:
                pass
        # Allow hostname format as well (but reject invalid dotted numeric quads)
        hostname_pattern = re.compile(
            r"^(localhost|(?=.{1,253}$)(?!-)([a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63})$"
        )
        if hostname_pattern.match(v):
            return v
        raise ValueError(f'Invalid IP address format: {v}')
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is a known value."""
        valid_statuses = ['active', 'inactive', 'maintenance', 'unknown']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}, got {v}')
        return v.lower()

    class Config:
        extra = 'allow'  # Allow additional fields


class DeviceListResponse(BaseModel):
    """Schema for paginated device list response."""
    devices: List[DeviceResponse] = Field(default_factory=list)


class DeviceCreateRequest(BaseModel):
    """Schema for creating a new device."""
    name: str = Field(..., min_length=1, max_length=100)
    ip_address: str = Field(...)
    device_type: str = Field(...)
    status: str = Field(default="active")
    vendor: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None


class DeviceUpdateRequest(BaseModel):
    """Schema for updating a device."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    ip_address: Optional[str] = None
    status: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None


class AlertResponse(BaseModel):
    """
    Schema for alert API response.
    """
    id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    severity: str = Field(...)
    message: str = Field(..., min_length=1)
    acknowledged: bool = Field(default=False)
    acknowledged_by: Optional[str] = None
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level."""
        valid_severities = ['critical', 'warning', 'info']
        if v.lower() not in valid_severities:
            raise ValueError(f'Severity must be one of {valid_severities}')
        return v.lower()

    class Config:
        extra = 'allow'


class AlertCreateRequest(BaseModel):
    """Schema for creating an alert."""
    device_id: str = Field(..., min_length=1)
    severity: str = Field(...)
    message: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Schema for user data in responses."""
    id: str = Field(...)
    username: str = Field(..., min_length=1)
    email: Optional[str] = None
    role: Optional[str] = None
    
    class Config:
        extra = 'allow'


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    token: str = Field(..., min_length=1, alias="token")  # API returns 'token' not 'access_token'
    token_type: str = Field(default="bearer")
    expires_in: Optional[int] = None
    user: Optional[dict] = None
    
    @field_validator('token_type')
    @classmethod
    def validate_token_type(cls, v: str) -> str:
        """Validate token type."""
        if v.lower() != "bearer":
            raise ValueError(f'Token type should be "bearer", got {v}')
        return v.lower()

    class Config:
        populate_by_name = True


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(...)
    database: Optional[str] = None
    timestamp: Optional[str] = None
    version: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_health_status(cls, v: str) -> str:
        """Validate health status."""
        valid_statuses = ['healthy', 'unhealthy', 'degraded']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Health status must be one of {valid_statuses}')
        return v.lower()


class PaginatedResponse(BaseModel):
    """Schema for paginated list responses."""
    items: List[dict] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    pages: int = Field(..., ge=0)


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str = Field(...)
    status_code: Optional[int] = None
    error_type: Optional[str] = None


# Type aliases for convenience
DeviceList = List[DeviceResponse]
AlertList = List[AlertResponse]

