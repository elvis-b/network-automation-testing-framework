"""
Device Service

Service layer abstraction for device API operations.
"""

import requests
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DeviceService:
    """
    Service class for device management operations.
    
    Provides a clean interface for tests to interact with
    device endpoints.
    """
    
    def __init__(self, base_url: str, session: requests.Session):
        """
        Initialize DeviceService.
        
        Args:
            base_url: API base URL
            session: Authenticated requests session
        """
        self.base_url = base_url
        self.session = session
    
    def get_all(
        self,
        status: Optional[str] = None,
        device_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get list of devices with optional filtering.
        
        Args:
            status: Filter by device status
            device_type: Filter by device type
            search: Search term for device name
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Response containing devices list and metadata
        """
        params = {"limit": limit, "offset": offset}
        
        if status:
            params["status"] = status
        if device_type:
            params["type"] = device_type
        if search:
            params["search"] = search
        
        response = self.session.get(
            f"{self.base_url}/devices",
            params=params
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_by_id(self, device_id: str) -> Dict[str, Any]:
        """
        Get device by ID.
        
        Args:
            device_id: Device unique identifier
            
        Returns:
            Device data
            
        Raises:
            requests.HTTPError: If device not found
        """
        response = self.session.get(f"{self.base_url}/devices/{device_id}")
        response.raise_for_status()
        
        return response.json()
    
    def create(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new device.
        
        Args:
            device_data: Device properties
            
        Returns:
            Created device data
        """
        logger.info(f"Creating device: {device_data.get('name')}")
        
        response = self.session.post(
            f"{self.base_url}/devices",
            json=device_data
        )
        response.raise_for_status()
        
        created = response.json()
        logger.info(f"Device created: {created.get('id')}")
        
        return created
    
    def update(self, device_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing device.
        
        Args:
            device_id: Device unique identifier
            update_data: Fields to update
            
        Returns:
            Updated device data
        """
        logger.info(f"Updating device: {device_id}")
        
        response = self.session.put(
            f"{self.base_url}/devices/{device_id}",
            json=update_data
        )
        response.raise_for_status()
        
        return response.json()
    
    def delete(self, device_id: str) -> None:
        """
        Delete a device.
        
        Args:
            device_id: Device unique identifier
        """
        logger.info(f"Deleting device: {device_id}")
        
        response = self.session.delete(f"{self.base_url}/devices/{device_id}")
        response.raise_for_status()
    
    def get_active_devices(self) -> List[Dict[str, Any]]:
        """
        Get all active devices.
        
        Returns:
            List of active devices
        """
        data = self.get_all(status="active")
        return data["devices"]
    
    def get_inactive_devices(self) -> List[Dict[str, Any]]:
        """
        Get all inactive devices.
        
        Returns:
            List of inactive devices
        """
        data = self.get_all(status="inactive")
        return data["devices"]
    
    def get_device_count(self) -> int:
        """
        Get total device count.
        
        Returns:
            Total number of devices
        """
        data = self.get_all(limit=1)
        return data["total"]
    
    def search_devices(self, query: str) -> List[Dict[str, Any]]:
        """
        Search devices by name.
        
        Args:
            query: Search term
            
        Returns:
            Matching devices
        """
        data = self.get_all(search=query)
        return data["devices"]
    
    def device_exists(self, device_id: str) -> bool:
        """
        Check if device exists.
        
        Args:
            device_id: Device unique identifier
            
        Returns:
            True if device exists
        """
        try:
            self.get_by_id(device_id)
            return True
        except requests.HTTPError:
            return False

