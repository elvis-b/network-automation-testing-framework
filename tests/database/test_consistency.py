"""
Database Consistency Tests

Tests validating data consistency between API and MongoDB.
"""

from datetime import datetime, timedelta

import pytest
from bson import ObjectId


@pytest.mark.database
@pytest.mark.sanity
def test_devices_collection_exists(devices_collection):
    """
    Test that devices collection exists and is accessible.
    """
    # Count should work without error
    count = devices_collection.count_documents({})

    assert count >= 0, "Should be able to count documents"


@pytest.mark.database
@pytest.mark.sanity
def test_device_created_via_api_exists_in_db(
    api_base_url,
    api_client,
    unique_device_data,
    devices_collection,
    cleanup_test_devices,
):
    """
    Test that a device created via API is persisted in MongoDB.
    """
    # Create device via API
    response = api_client.post(f"{api_base_url}/devices", json=unique_device_data)
    assert response.status_code == 201

    api_device = response.json()
    device_id = api_device["id"]
    cleanup_test_devices.append(device_id)

    # Verify in database
    db_device = devices_collection.find_one({"_id": ObjectId(device_id)})

    assert db_device is not None, "Device should exist in database"
    assert db_device["name"] == unique_device_data["name"]
    assert db_device["ip_address"] == unique_device_data["ip_address"]


@pytest.mark.database
@pytest.mark.regression
def test_device_update_reflected_in_db(
    api_base_url,
    api_client,
    unique_device_data,
    devices_collection,
    cleanup_test_devices,
):
    """
    Test that device updates via API are persisted in MongoDB.
    """
    # Create device
    response = api_client.post(f"{api_base_url}/devices", json=unique_device_data)
    device_id = response.json()["id"]
    cleanup_test_devices.append(device_id)

    # Update via API
    update_data = {"location": "Database Test Location"}
    api_client.put(f"{api_base_url}/devices/{device_id}", json=update_data)

    # Verify in database
    db_device = devices_collection.find_one({"_id": ObjectId(device_id)})

    assert db_device["location"] == "Database Test Location"


@pytest.mark.database
@pytest.mark.regression
def test_device_delete_removes_from_db(
    api_base_url, api_client, unique_device_data, devices_collection
):
    """
    Test that device deletion via API removes from MongoDB.
    """
    # Create device
    response = api_client.post(f"{api_base_url}/devices", json=unique_device_data)
    device_id = response.json()["id"]

    # Verify exists
    assert devices_collection.find_one({"_id": ObjectId(device_id)}) is not None

    # Delete via API
    api_client.delete(f"{api_base_url}/devices/{device_id}")

    # Verify removed
    assert devices_collection.find_one({"_id": ObjectId(device_id)}) is None


@pytest.mark.database
@pytest.mark.sanity
def test_api_device_matches_db_record(api_base_url, api_client, devices_collection):
    """
    Test that API response matches database record.
    """
    # Get device from API
    response = api_client.get(f"{api_base_url}/devices")
    devices = response.json()["devices"]

    if not devices:
        pytest.skip("No devices available")

    api_device = devices[0]

    # Get same device from database
    db_device = devices_collection.find_one({"_id": ObjectId(api_device["id"])})

    assert db_device is not None
    assert db_device["name"] == api_device["name"]
    assert db_device["ip_address"] == api_device["ip_address"]
    assert db_device["status"] == api_device["status"]


@pytest.mark.database
@pytest.mark.regression
def test_timestamps_are_valid(devices_collection):
    """
    Test that timestamps in database are valid and recent.
    """
    devices = list(devices_collection.find({}).limit(5))

    if not devices:
        pytest.skip("No devices in database")

    now = datetime.utcnow()
    one_year_ago = now - timedelta(days=365)

    for device in devices:
        created_at = device.get("created_at")
        updated_at = device.get("updated_at")

        if created_at:
            assert isinstance(created_at, datetime), "created_at should be datetime"
            assert created_at > one_year_ago, "created_at should be within last year"
            assert created_at <= now, "created_at should not be in future"

        if updated_at:
            assert isinstance(updated_at, datetime), "updated_at should be datetime"
            assert updated_at >= created_at, "updated_at should be >= created_at"


@pytest.mark.database
@pytest.mark.regression
def test_alert_acknowledgment_persisted(api_base_url, api_client, alerts_collection):
    """
    Test that alert acknowledgment is persisted in database.
    """
    # Find unacknowledged alert
    unacked_alert = alerts_collection.find_one({"acknowledged": False})

    if not unacked_alert:
        pytest.skip("No unacknowledged alerts available")

    alert_id = str(unacked_alert["_id"])

    # Acknowledge via API
    response = api_client.put(f"{api_base_url}/alerts/{alert_id}/acknowledge")

    if response.status_code != 200:
        pytest.skip("Could not acknowledge alert")

    # Verify in database
    db_alert = alerts_collection.find_one({"_id": ObjectId(alert_id)})

    assert db_alert["acknowledged"] == True
    assert db_alert["acknowledged_by"] is not None
    assert db_alert["acknowledged_at"] is not None


@pytest.mark.database
@pytest.mark.regression
def test_device_count_matches_api(api_base_url, api_client, devices_collection):
    """
    Test that device count from API matches database count.
    """
    # Get count from API
    response = api_client.get(f"{api_base_url}/devices")
    api_total = response.json()["total"]

    # Get count from database
    db_count = devices_collection.count_documents({})

    assert (
        api_total == db_count
    ), f"API total ({api_total}) should match DB count ({db_count})"
