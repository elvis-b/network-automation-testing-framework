"""
Network Helper Utilities

Provides utilities for network-related operations in tests:
- Device connectivity checks
- Interface validation
- Network parsing helpers
"""

import os
import socket
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InterfaceStatus:
    """Represents network interface status."""
    name: str
    ip_address: Optional[str]
    status: str
    protocol: str
    description: Optional[str] = None


@dataclass
class DeviceInfo:
    """Represents network device information."""
    hostname: str
    platform: str
    version: str
    uptime: Optional[str] = None
    serial: Optional[str] = None


class NetworkHelper:
    """
    Helper class for network operations in tests.
    
    Provides methods for:
    - Connectivity testing
    - PyATS device interactions
    - Interface parsing
    - Network validation
    """

    def __init__(self, testbed=None):
        """
        Initialize NetworkHelper.
        
        Args:
            testbed: PyATS testbed object (optional)
        """
        self.testbed = testbed
        self._connected_devices: Dict[str, Any] = {}

    @staticmethod
    def is_host_reachable(host: str, port: int = 22, timeout: float = 5.0) -> bool:
        """
        Check if a host is reachable on a specific port.
        
        Args:
            host: Hostname or IP address
            port: Port number to check
            timeout: Connection timeout in seconds
            
        Returns:
            True if host is reachable
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            is_reachable = result == 0
            logger.info(f"Host {host}:{port} reachable: {is_reachable}")
            return is_reachable
        except socket.error as e:
            logger.warning(f"Socket error checking {host}:{port}: {e}")
            return False

    @staticmethod
    def is_valid_ip(ip_address: str) -> bool:
        """
        Validate an IP address format.
        
        Args:
            ip_address: IP address string to validate
            
        Returns:
            True if valid IPv4 or IPv6 address
        """
        try:
            socket.inet_aton(ip_address)
            return True
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, ip_address)
                return True
            except socket.error:
                return False

    def connect_device(self, device_name: str) -> Optional[Any]:
        """
        Connect to a device from the testbed.
        
        Args:
            device_name: Name of device in testbed
            
        Returns:
            Connected device object or None
        """
        if self.testbed is None:
            logger.warning("No testbed configured")
            return None
        
        if device_name not in self.testbed.devices:
            logger.warning(f"Device {device_name} not in testbed")
            return None
        
        if device_name in self._connected_devices:
            return self._connected_devices[device_name]
        
        device = self.testbed.devices[device_name]
        
        try:
            device.connect(log_stdout=False, connection_timeout=30)
            self._connected_devices[device_name] = device
            logger.info(f"Connected to {device_name}")
            return device
        except Exception as e:
            logger.error(f"Failed to connect to {device_name}: {e}")
            return None

    def disconnect_device(self, device_name: str) -> None:
        """
        Disconnect from a device.
        
        Args:
            device_name: Name of device to disconnect
        """
        if device_name in self._connected_devices:
            device = self._connected_devices[device_name]
            if device.is_connected():
                device.disconnect()
                logger.info(f"Disconnected from {device_name}")
            del self._connected_devices[device_name]

    def disconnect_all(self) -> None:
        """Disconnect from all connected devices."""
        for device_name in list(self._connected_devices.keys()):
            self.disconnect_device(device_name)

    def get_device_info(self, device) -> Optional[DeviceInfo]:
        """
        Get device information using show version.
        
        Args:
            device: Connected PyATS device object
            
        Returns:
            DeviceInfo dataclass or None
        """
        try:
            output = device.parse("show version")
            
            # Extract info (structure varies by platform)
            version_info = output.get("version", {})
            
            return DeviceInfo(
                hostname=version_info.get("hostname", device.name),
                platform=version_info.get("platform", "unknown"),
                version=version_info.get("version", "unknown"),
                uptime=version_info.get("uptime", None),
                serial=version_info.get("serial_number", None)
            )
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None

    def get_interfaces(self, device) -> List[InterfaceStatus]:
        """
        Get interface status from device.
        
        Args:
            device: Connected PyATS device object
            
        Returns:
            List of InterfaceStatus objects
        """
        interfaces = []
        
        try:
            output = device.parse("show ip interface brief")
            
            for name, data in output.get("interface", {}).items():
                interfaces.append(InterfaceStatus(
                    name=name,
                    ip_address=data.get("ip_address"),
                    status=data.get("status", "unknown"),
                    protocol=data.get("protocol", "unknown"),
                    description=data.get("description")
                ))
        except Exception as e:
            logger.error(f"Failed to get interfaces: {e}")
        
        return interfaces

    def get_up_interfaces(self, device) -> List[InterfaceStatus]:
        """
        Get only interfaces that are UP.
        
        Args:
            device: Connected PyATS device object
            
        Returns:
            List of InterfaceStatus for UP interfaces
        """
        all_interfaces = self.get_interfaces(device)
        return [iface for iface in all_interfaces if iface.status.lower() == "up"]

    def validate_interface_count(
        self,
        device,
        min_up: int = 1,
        min_total: int = 1
    ) -> Tuple[bool, str]:
        """
        Validate interface counts meet requirements.
        
        Args:
            device: Connected PyATS device object
            min_up: Minimum number of UP interfaces required
            min_total: Minimum total interfaces required
            
        Returns:
            Tuple of (is_valid, message)
        """
        interfaces = self.get_interfaces(device)
        up_interfaces = [i for i in interfaces if i.status.lower() == "up"]
        
        total_count = len(interfaces)
        up_count = len(up_interfaces)
        
        if total_count < min_total:
            return False, f"Total interfaces ({total_count}) < required ({min_total})"
        
        if up_count < min_up:
            return False, f"UP interfaces ({up_count}) < required ({min_up})"
        
        return True, f"Validated: {up_count} UP of {total_count} total interfaces"

    def execute_command(self, device, command: str) -> str:
        """
        Execute a command on device and return output.
        
        Args:
            device: Connected PyATS device object
            command: Command to execute
            
        Returns:
            Command output string
        """
        try:
            output = device.execute(command)
            return output
        except Exception as e:
            logger.error(f"Failed to execute '{command}': {e}")
            return ""

    def parse_command(self, device, command: str) -> Dict[str, Any]:
        """
        Execute and parse a command using Genie parser.
        
        Args:
            device: Connected PyATS device object
            command: Command to parse
            
        Returns:
            Parsed output dictionary
        """
        try:
            return device.parse(command)
        except Exception as e:
            logger.error(f"Failed to parse '{command}': {e}")
            return {}

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect all devices."""
        self.disconnect_all()

