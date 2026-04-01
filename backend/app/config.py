"""
Application Configuration

Centralized configuration management using environment variables.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Network Monitoring API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 5000

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_database: str = "network_monitoring"

    # JWT Authentication
    jwt_secret: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Network (DevNet Sandbox)
    devnet_host: str = "sandbox-iosxe-latest-1.cisco.com"
    devnet_port: int = 22
    devnet_username: str = "developer"
    devnet_password: str = "C1sco12345"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()


# Export settings instance
settings = get_settings()
