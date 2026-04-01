"""
Database Helper Utilities

Provides utilities for database operations in tests:
- Data seeding
- Data cleanup
- Query helpers
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId

logger = logging.getLogger(__name__)


class DatabaseHelper:
    """
    Helper class for database operations in tests.
    
    Provides methods for:
    - Connecting to MongoDB
    - Seeding test data
    - Cleaning up test data
    - Querying collections
    """

    def __init__(
        self,
        mongodb_uri: Optional[str] = None,
        database_name: Optional[str] = None
    ):
        """
        Initialize DatabaseHelper.
        
        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Name of database to use
        """
        self.mongodb_uri = mongodb_uri or os.getenv(
            "MONGODB_URI", "mongodb://localhost:27017/"
        )
        self.database_name = database_name or os.getenv(
            "MONGODB_DATABASE", "network_monitoring"
        )
        self._client: Optional[MongoClient] = None
        self._test_data_ids: Dict[str, List[str]] = {
            "devices": [],
            "alerts": [],
            "users": []
        }

    @property
    def client(self) -> MongoClient:
        """Get MongoDB client, creating if necessary."""
        if self._client is None:
            self._client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            # Verify connection
            self._client.admin.command("ping")
            logger.info(f"Connected to MongoDB at {self.mongodb_uri}")
        return self._client

    @property
    def database(self):
        """Get database instance."""
        return self.client[self.database_name]

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a collection by name.
        
        Args:
            collection_name: Name of collection
            
        Returns:
            MongoDB Collection
        """
        return self.database[collection_name]

    def seed_from_json(self, json_path: str, collection_name: str) -> List[str]:
        """
        Seed collection with data from JSON file.
        
        Args:
            json_path: Path to JSON file
            collection_name: Target collection name
            
        Returns:
            List of inserted document IDs
        """
        path = Path(json_path)
        if not path.exists():
            logger.warning(f"JSON file not found: {json_path}")
            return []
        
        with open(path, "r") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        # Add timestamps
        for doc in data:
            doc.setdefault("created_at", datetime.utcnow())
            doc.setdefault("updated_at", datetime.utcnow())
        
        collection = self.get_collection(collection_name)
        result = collection.insert_many(data)
        
        inserted_ids = [str(id) for id in result.inserted_ids]
        self._test_data_ids[collection_name].extend(inserted_ids)
        
        logger.info(f"Seeded {len(inserted_ids)} documents into {collection_name}")
        return inserted_ids

    def seed_test_device(self, device_data: Dict[str, Any]) -> str:
        """
        Seed a single test device.
        
        Args:
            device_data: Device data dictionary
            
        Returns:
            Inserted document ID
        """
        device_data.setdefault("created_at", datetime.utcnow())
        device_data.setdefault("updated_at", datetime.utcnow())
        device_data.setdefault("status", "active")
        
        collection = self.get_collection("devices")
        result = collection.insert_one(device_data)
        
        device_id = str(result.inserted_id)
        self._test_data_ids["devices"].append(device_id)
        
        logger.info(f"Seeded test device: {device_data.get('name')} ({device_id})")
        return device_id

    def seed_test_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Seed a single test alert.
        
        Args:
            alert_data: Alert data dictionary
            
        Returns:
            Inserted document ID
        """
        alert_data.setdefault("timestamp", datetime.utcnow())
        alert_data.setdefault("acknowledged", False)
        
        collection = self.get_collection("alerts")
        result = collection.insert_one(alert_data)
        
        alert_id = str(result.inserted_id)
        self._test_data_ids["alerts"].append(alert_id)
        
        logger.info(f"Seeded test alert: {alert_data.get('message')} ({alert_id})")
        return alert_id

    def cleanup_test_data(self) -> None:
        """
        Remove all test data created by this helper.
        
        Should be called in test teardown.
        """
        for collection_name, ids in self._test_data_ids.items():
            if ids:
                collection = self.get_collection(collection_name)
                object_ids = [ObjectId(id) for id in ids]
                result = collection.delete_many({"_id": {"$in": object_ids}})
                logger.info(
                    f"Cleaned up {result.deleted_count} documents from {collection_name}"
                )
                ids.clear()

    def cleanup_collection(self, collection_name: str) -> int:
        """
        Remove all documents from a collection.
        
        Use with caution - removes ALL data.
        
        Args:
            collection_name: Collection to clear
            
        Returns:
            Number of documents deleted
        """
        collection = self.get_collection(collection_name)
        result = collection.delete_many({})
        logger.warning(f"Cleared {result.deleted_count} documents from {collection_name}")
        return result.deleted_count

    def count_documents(self, collection_name: str, query: Optional[Dict] = None) -> int:
        """
        Count documents in a collection.
        
        Args:
            collection_name: Collection to count
            query: Optional query filter
            
        Returns:
            Document count
        """
        collection = self.get_collection(collection_name)
        return collection.count_documents(query or {})

    def find_one(
        self,
        collection_name: str,
        query: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document.
        
        Args:
            collection_name: Collection to search
            query: Query filter
            
        Returns:
            Document or None
        """
        collection = self.get_collection(collection_name)
        return collection.find_one(query)

    def find_by_id(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find document by ID.
        
        Args:
            collection_name: Collection to search
            document_id: Document ID string
            
        Returns:
            Document or None
        """
        return self.find_one(collection_name, {"_id": ObjectId(document_id)})

    def close(self) -> None:
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup and close."""
        self.cleanup_test_data()
        self.close()

