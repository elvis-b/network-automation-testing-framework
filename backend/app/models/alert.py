"""
Alert Models

Pydantic models for alert data validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertType(str, Enum):
    """Alert type enumeration."""
    CONNECTIVITY = "connectivity"
    PERFORMANCE = "performance"
    SECURITY = "security"


class AlertBase(BaseModel):
    """Base alert model with common fields."""
    device_id: str
    device_name: str
    severity: AlertSeverity
    type: AlertType
    message: str = Field(..., min_length=1, max_length=500)


class AlertCreate(AlertBase):
    """Model for creating a new alert."""
    pass


class AlertUpdate(BaseModel):
    """Model for updating an alert."""
    severity: Optional[AlertSeverity] = None
    message: Optional[str] = Field(None, min_length=1, max_length=500)


class AlertInDB(AlertBase):
    """Alert model as stored in database."""
    id: str = Field(..., alias="_id")
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class AlertResponse(AlertBase):
    """Alert model for API responses."""
    id: str
    timestamp: datetime
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Alert(AlertBase):
    """Full alert model."""
    id: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertListResponse(BaseModel):
    """Response model for alert list endpoint."""
    alerts: List[AlertResponse]
    total: int


class AcknowledgeResponse(BaseModel):
    """Response model for acknowledge endpoint."""
    id: str
    acknowledged: bool
    acknowledged_by: str
    acknowledged_at: datetime

