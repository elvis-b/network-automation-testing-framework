from datetime import datetime

import pytest
import requests


@pytest.mark.api
@pytest.mark.smoke
def test_get_all_alerts(api_base_url, api_client):
    """
    Test GET /alerts returns list of alerts.
    """
    response = api_client.get(f"{api_base_url}/alerts")

    assert response.status_code == 200, f"Failed to get alerts: {response.text}"

    data = response.json()
    assert "alerts" in data, "Response should include 'alerts' list"
    assert "total" in data, "Response should include 'total' count"
    assert isinstance(data["alerts"], list)


@pytest.mark.api
@pytest.mark.sanity
def test_get_alerts_returns_expected_fields(api_base_url, api_client):
    """
    Test that alert objects contain expected fields.
    """
    response = api_client.get(f"{api_base_url}/alerts")
    data = response.json()

    if data["total"] > 0:
        alert = data["alerts"][0]

        expected_fields = [
            "id",
            "device_id",
            "device_name",
            "severity",
            "type",
            "message",
            "timestamp",
            "acknowledged",
        ]
        for field in expected_fields:
            assert field in alert, f"Alert should have '{field}' field"


@pytest.mark.api
@pytest.mark.regression
def test_get_alerts_filter_by_severity(api_base_url, api_client):
    """
    Test filtering alerts by severity.
    """
    response = api_client.get(f"{api_base_url}/alerts", params={"severity": "critical"})

    assert response.status_code == 200
    data = response.json()

    for alert in data["alerts"]:
        assert alert["severity"] == "critical"


@pytest.mark.api
@pytest.mark.regression
def test_get_alerts_filter_by_acknowledged(api_base_url, api_client):
    """
    Test filtering alerts by acknowledgment status.
    """
    # Get unacknowledged alerts
    response = api_client.get(
        f"{api_base_url}/alerts", params={"acknowledged": "false"}
    )

    assert response.status_code == 200
    data = response.json()

    for alert in data["alerts"]:
        assert alert["acknowledged"] == False


@pytest.mark.api
@pytest.mark.sanity
def test_get_alert_by_id(api_base_url, api_client):
    """
    Test GET /alerts/{id} returns specific alert.
    """
    # First get all alerts
    list_response = api_client.get(f"{api_base_url}/alerts")
    alerts = list_response.json()["alerts"]

    if not alerts:
        pytest.skip("No alerts available for testing")

    alert_id = alerts[0]["id"]

    # Get specific alert
    response = api_client.get(f"{api_base_url}/alerts/{alert_id}")

    assert response.status_code == 200
    alert = response.json()
    assert alert["id"] == alert_id


@pytest.mark.api
@pytest.mark.regression
def test_get_alert_not_found(api_base_url, api_client):
    """
    Test GET /alerts/{id} returns 404 for nonexistent alert.
    """
    fake_id = "000000000000000000000000"

    response = api_client.get(f"{api_base_url}/alerts/{fake_id}")

    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.sanity
def test_acknowledge_alert(api_base_url, api_client):
    """
    Test PUT /alerts/{id}/acknowledge acknowledges an alert.
    """
    # Get unacknowledged alert
    list_response = api_client.get(
        f"{api_base_url}/alerts", params={"acknowledged": "false"}
    )
    alerts = list_response.json()["alerts"]

    if not alerts:
        pytest.skip("No unacknowledged alerts available for testing")

    alert_id = alerts[0]["id"]

    # Acknowledge alert
    response = api_client.put(f"{api_base_url}/alerts/{alert_id}/acknowledge")

    assert response.status_code == 200

    data = response.json()
    assert data["acknowledged"] == True
    assert data["acknowledged_by"] is not None
    assert data["acknowledged_at"] is not None


@pytest.mark.api
@pytest.mark.regression
def test_acknowledge_already_acknowledged_alert(api_base_url, api_client):
    """
    Test acknowledging an already acknowledged alert returns error.
    """
    # Get acknowledged alert
    list_response = api_client.get(
        f"{api_base_url}/alerts", params={"acknowledged": "true"}
    )
    alerts = list_response.json()["alerts"]

    if not alerts:
        pytest.skip("No acknowledged alerts available for testing")

    alert_id = alerts[0]["id"]

    # Try to acknowledge again
    response = api_client.put(f"{api_base_url}/alerts/{alert_id}/acknowledge")

    assert response.status_code == 400
    assert "already acknowledged" in response.json()["detail"].lower()


@pytest.mark.api
@pytest.mark.regression
def test_acknowledge_alert_not_found(api_base_url, api_client):
    """
    Test acknowledging nonexistent alert returns 404.
    """
    fake_id = "000000000000000000000000"

    response = api_client.put(f"{api_base_url}/alerts/{fake_id}/acknowledge")

    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.regression
def test_create_alert(api_base_url, api_client, test_alert_data):
    """
    Test POST /alerts creates a new alert.
    """
    response = api_client.post(f"{api_base_url}/alerts", json=test_alert_data)

    assert response.status_code == 201

    alert = response.json()
    assert "id" in alert
    assert alert["severity"] == test_alert_data["severity"]
    assert alert["message"] == test_alert_data["message"]
    assert alert["acknowledged"] == False


@pytest.mark.api
@pytest.mark.regression
def test_alerts_sorted_by_severity(api_base_url, api_client):
    """
    Test that unacknowledged alerts are sorted by severity (critical first).
    """
    response = api_client.get(
        f"{api_base_url}/alerts", params={"acknowledged": "false"}
    )
    alerts = response.json()["alerts"]

    if len(alerts) < 2:
        pytest.skip("Not enough alerts to test sorting")

    severity_order = {"critical": 0, "warning": 1, "info": 2}

    for i in range(len(alerts) - 1):
        current_severity = severity_order.get(alerts[i]["severity"], 99)
        next_severity = severity_order.get(alerts[i + 1]["severity"], 99)

        # Current should be equal or higher priority (lower number)
        assert (
            current_severity <= next_severity
        ), f"Alerts not sorted correctly: {alerts[i]['severity']} should come before {alerts[i+1]['severity']}"


@pytest.mark.api
@pytest.mark.regression
def test_get_alerts_skips_malformed_legacy_documents(
    api_base_url, api_client, alerts_collection
):
    """GET /alerts should tolerate malformed legacy documents."""
    suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

    valid_message = f"test-valid-alert-{suffix}"
    malformed_message = f"test-malformed-alert-{suffix}"

    alerts_collection.insert_one(
        {
            "device_id": "legacy-device-001",
            "device_name": "legacy-router-01",
            "severity": "warning",
            "type": "performance",
            "message": valid_message,
            "acknowledged": False,
            "timestamp": datetime.utcnow(),
        }
    )
    alerts_collection.insert_one(
        {
            # Missing device_id on purpose (legacy malformed document)
            "device_name": "legacy-router-02",
            "severity": "critical",
            "type": "connectivity",
            "message": malformed_message,
            "acknowledged": False,
            "timestamp": datetime.utcnow(),
        }
    )

    response = api_client.get(f"{api_base_url}/alerts")
    assert response.status_code == 200, f"Failed to get alerts: {response.text}"

    data = response.json()
    messages = [alert["message"] for alert in data["alerts"]]

    assert valid_message in messages
    assert malformed_message not in messages


@pytest.mark.api
@pytest.mark.regression
def test_get_alert_by_id_returns_422_for_malformed_document(
    api_base_url, api_client, alerts_collection
):
    """GET /alerts/{id} should return 422 for malformed legacy documents."""
    malformed_alert = alerts_collection.insert_one(
        {
            # Missing device_id on purpose (legacy malformed document)
            "device_name": "legacy-router-by-id",
            "severity": "critical",
            "type": "connectivity",
            "message": "test-malformed-alert-by-id",
            "acknowledged": False,
            "timestamp": datetime.utcnow(),
        }
    )

    response = api_client.get(f"{api_base_url}/alerts/{malformed_alert.inserted_id}")
    assert response.status_code == 422
    assert "malformed" in response.json().get("detail", "").lower()
