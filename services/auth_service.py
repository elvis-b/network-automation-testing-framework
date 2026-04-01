"""
Authentication Service

Service layer abstraction for authentication API operations.
"""

import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service class for authentication operations.

    Provides a clean interface for tests to interact with
    authentication endpoints.
    """

    def __init__(self, base_url: str, session: Optional[requests.Session] = None):
        """
        Initialize AuthService.

        Args:
            base_url: API base URL (e.g., http://localhost:5000/api)
            session: Optional requests session for connection pooling
        """
        self.base_url = base_url
        self.session = session or requests.Session()
        self._token: Optional[str] = None

    @property
    def token(self) -> Optional[str]:
        """Get current authentication token."""
        return self._token

    @property
    def is_authenticated(self) -> bool:
        """Check if service has a valid token."""
        return self._token is not None

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and store token.

        Args:
            username: User's username
            password: User's password

        Returns:
            Login response data including token and user info

        Raises:
            requests.HTTPError: If login fails
        """
        logger.info(f"Logging in as {username}")

        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
        )
        response.raise_for_status()

        data = response.json()
        self._token = data.get("token")

        # Update session headers
        if self._token:
            self.session.headers["Authorization"] = f"Bearer {self._token}"

        logger.info(f"Login successful for {username}")
        return data

    def logout(self) -> Dict[str, Any]:
        """
        Logout current user.

        Returns:
            Logout response data
        """
        logger.info("Logging out")

        response = self.session.post(f"{self.base_url}/auth/logout")
        response.raise_for_status()

        # Clear token
        self._token = None
        self.session.headers.pop("Authorization", None)

        return response.json()

    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current authenticated user info.

        Returns:
            User data

        Raises:
            requests.HTTPError: If not authenticated or request fails
        """
        response = self.session.get(f"{self.base_url}/auth/me")
        response.raise_for_status()

        return response.json()

    def refresh_token(self) -> Dict[str, Any]:
        """
        Refresh authentication token.

        Returns:
            New token data
        """
        response = self.session.post(f"{self.base_url}/auth/refresh")
        response.raise_for_status()

        data = response.json()
        self._token = data.get("access_token")

        if self._token:
            self.session.headers["Authorization"] = f"Bearer {self._token}"

        return data

    def verify_token(self, token: str) -> bool:
        """
        Verify if a token is valid by attempting to use it.

        Args:
            token: JWT token to verify

        Returns:
            True if token is valid, False otherwise
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = self.session.get(f"{self.base_url}/auth/me", headers=headers)

        return response.status_code == 200
