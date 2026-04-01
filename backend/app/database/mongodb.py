"""
MongoDB Database Connection

Handles MongoDB connection lifecycle and provides database access.
"""

import logging
from typing import Optional

from app.config import settings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


db = MongoDB()


async def connect_to_mongo() -> None:
    """
    Establish connection to MongoDB.

    Called during application startup.
    """
    logger.info(f"Connecting to MongoDB at {settings.mongodb_uri}")

    db.client = AsyncIOMotorClient(
        settings.mongodb_uri,
        maxPoolSize=10,
        minPoolSize=1,
        serverSelectionTimeoutMS=5000,
    )
    db.database = db.client[settings.mongodb_database]

    # Verify connection
    try:
        await db.client.admin.command("ping")
        logger.info("MongoDB connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """
    Close MongoDB connection.

    Called during application shutdown.
    """
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance

    Raises:
        RuntimeError: If database is not connected
    """
    if db.database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return db.database


async def get_collection(collection_name: str):
    """
    Get a collection from the database.

    Args:
        collection_name: Name of the collection

    Returns:
        Collection instance
    """
    database = get_database()
    return database[collection_name]


async def seed_database() -> None:
    """
    Seed database with initial data.

    Creates default users, devices, and alerts for testing.
    """
    from datetime import datetime

    from app.models.alert import AlertCreate
    from app.models.device import DeviceCreate
    from app.models.user import UserCreate
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    database = get_database()

    # Seed users
    users_collection = database["users"]
    existing_users = await users_collection.count_documents({})

    if existing_users == 0:
        default_users = [
            {
                "username": "admin",
                "password_hash": pwd_context.hash("admin123"),
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
            },
            {
                "username": "operator",
                "password_hash": pwd_context.hash("operator123"),
                "email": "operator@example.com",
                "role": "operator",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
            },
            {
                "username": "viewer",
                "password_hash": pwd_context.hash("viewer123"),
                "email": "viewer@example.com",
                "role": "viewer",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
            },
        ]
        await users_collection.insert_many(default_users)
        logger.info("Seeded default users")

    # Seed devices
    devices_collection = database["devices"]
    existing_devices = await devices_collection.count_documents({})

    if existing_devices == 0:
        default_devices = [
            {
                "name": "core-router-01",
                "ip_address": "10.0.0.1",
                "device_type": "router",
                "vendor": "cisco",
                "model": "CSR1000v",
                "status": "active",
                "location": "Data Center 1",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "metadata": {"os_version": "IOS-XE 17.3", "uptime": 864000},
            },
            {
                "name": "core-router-02",
                "ip_address": "10.0.0.2",
                "device_type": "router",
                "vendor": "cisco",
                "model": "CSR1000v",
                "status": "active",
                "location": "Data Center 1",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "metadata": {"os_version": "IOS-XE 17.3", "uptime": 432000},
            },
            {
                "name": "dist-switch-01",
                "ip_address": "10.0.1.1",
                "device_type": "switch",
                "vendor": "cisco",
                "model": "Catalyst 9300",
                "status": "active",
                "location": "Building A",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "metadata": {"os_version": "IOS-XE 17.6", "uptime": 1728000},
            },
            {
                "name": "dist-switch-02",
                "ip_address": "10.0.1.2",
                "device_type": "switch",
                "vendor": "cisco",
                "model": "Catalyst 9300",
                "status": "inactive",
                "location": "Building B",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "metadata": {"os_version": "IOS-XE 17.6", "uptime": 0},
            },
            {
                "name": "edge-firewall-01",
                "ip_address": "10.0.2.1",
                "device_type": "firewall",
                "vendor": "cisco",
                "model": "ASA 5525-X",
                "status": "active",
                "location": "DMZ",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "metadata": {"os_version": "ASA 9.16", "uptime": 2592000},
            },
        ]
        await devices_collection.insert_many(default_devices)
        logger.info("Seeded default devices")

    # Seed alerts
    alerts_collection = database["alerts"]
    existing_alerts = await alerts_collection.count_documents({})

    if existing_alerts == 0:
        # Get device IDs
        devices = await devices_collection.find({}).to_list(length=100)
        device_map = {d["name"]: str(d["_id"]) for d in devices}

        default_alerts = [
            {
                "device_id": device_map.get("core-router-01"),
                "device_name": "core-router-01",
                "severity": "critical",
                "type": "performance",
                "message": "High CPU utilization detected (95%)",
                "timestamp": datetime.utcnow(),
                "acknowledged": False,
                "acknowledged_by": None,
                "acknowledged_at": None,
                "resolved": False,
                "resolved_at": None,
            },
            {
                "device_id": device_map.get("dist-switch-02"),
                "device_name": "dist-switch-02",
                "severity": "warning",
                "type": "connectivity",
                "message": "Interface GigabitEthernet0/1 is down",
                "timestamp": datetime.utcnow(),
                "acknowledged": False,
                "acknowledged_by": None,
                "acknowledged_at": None,
                "resolved": False,
                "resolved_at": None,
            },
            {
                "device_id": device_map.get("edge-firewall-01"),
                "device_name": "edge-firewall-01",
                "severity": "info",
                "type": "security",
                "message": "Configuration backup completed successfully",
                "timestamp": datetime.utcnow(),
                "acknowledged": True,
                "acknowledged_by": "admin",
                "acknowledged_at": datetime.utcnow(),
                "resolved": True,
                "resolved_at": datetime.utcnow(),
            },
        ]
        await alerts_collection.insert_many(default_alerts)
        logger.info("Seeded default alerts")
