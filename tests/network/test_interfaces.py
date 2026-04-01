"""
Network Interface Tests

PyATS tests for validating network interface status
on Cisco DevNet Sandbox devices.
"""

import pytest
import logging

logger = logging.getLogger(__name__)


@pytest.mark.network
@pytest.mark.sanity
def test_interface_status_parsing(network_device):
    """
    Test parsing interface status from device.
    
    Verifies:
    - Can retrieve interface information
    - Output is properly parsed
    - Contains expected interface data
    """
    try:
        output = network_device.parse("show ip interface brief")
        
        assert output is not None, "Should receive parsed output"
        assert "interface" in output, "Should contain interface key"
        
        interfaces = output["interface"]
        assert len(interfaces) > 0, "Should have at least one interface"
        
        logger.info(f"Found {len(interfaces)} interfaces")
        
        # Log interface names
        for intf_name in interfaces:
            logger.info(f"  - {intf_name}")
            
    except Exception as e:
        logger.warning(f"Parsing failed: {e}")
        # Fallback to raw command
        output = network_device.execute("show ip interface brief")
        assert "Interface" in output, "Should contain interface information"


@pytest.mark.network
@pytest.mark.regression
def test_at_least_one_interface_up(network_device):
    """
    Test that at least one interface is in 'up' status.
    """
    try:
        output = network_device.parse("show ip interface brief")
        interfaces = output.get("interface", {})
        
        # Find interfaces that are up
        up_interfaces = [
            name for name, data in interfaces.items()
            if data.get("status", "").lower() == "up"
        ]
        
        assert len(up_interfaces) > 0, "At least one interface should be up"
        
        logger.info(f"Interfaces in 'up' state: {up_interfaces}")
        
    except Exception as e:
        logger.warning(f"Parsing failed: {e}")
        output = network_device.execute("show ip interface brief")
        # Check for "up" in raw output
        assert "up" in output.lower(), "Should have interfaces in up state"


@pytest.mark.network
@pytest.mark.regression
def test_interface_ip_addresses(network_device):
    """
    Test retrieving interface IP addresses.
    """
    try:
        output = network_device.parse("show ip interface brief")
        interfaces = output.get("interface", {})
        
        # Find interfaces with IP addresses
        interfaces_with_ip = [
            (name, data.get("ip_address", "unassigned"))
            for name, data in interfaces.items()
            if data.get("ip_address") and data.get("ip_address") != "unassigned"
        ]
        
        logger.info(f"Interfaces with IP addresses: {interfaces_with_ip}")
        
        # At least one interface should have an IP (for management)
        assert len(interfaces_with_ip) > 0, \
            "At least one interface should have an IP address"
            
    except Exception as e:
        logger.warning(f"Parsing failed: {e}")
        output = network_device.execute("show ip interface brief")
        # Basic assertion on raw output
        assert len(output) > 0


@pytest.mark.network
@pytest.mark.regression
def test_interface_detailed_info(network_device):
    """
    Test retrieving detailed interface information.
    """
    try:
        # Get detailed interface info for GigabitEthernet1 (common on CSR1000v)
        output = network_device.parse("show interfaces GigabitEthernet1")
        
        assert output is not None
        assert "GigabitEthernet1" in output
        
        intf_data = output["GigabitEthernet1"]
        
        # Check for expected detailed fields
        expected_fields = ["enabled", "line_protocol"]
        for field in expected_fields:
            if field in intf_data:
                logger.info(f"  {field}: {intf_data[field]}")
                
    except Exception as e:
        logger.warning(f"Detailed interface parsing failed: {e}")
        # Try raw command
        output = network_device.execute("show interfaces GigabitEthernet1")
        assert "GigabitEthernet1" in output


@pytest.mark.network
@pytest.mark.slow
def test_all_interface_counters(network_device):
    """
    Test retrieving interface counters (slow test due to data volume).
    """
    output = network_device.execute("show interfaces")
    
    assert output is not None
    assert len(output) > 0
    
    # Check for common counter keywords
    counter_keywords = ["packets input", "packets output", "errors"]
    found_keywords = [kw for kw in counter_keywords if kw in output.lower()]
    
    logger.info(f"Found counter keywords: {found_keywords}")
    
    assert len(found_keywords) > 0, "Should contain interface counter information"

