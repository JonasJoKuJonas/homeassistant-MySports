"""
MySports API Wrapper for Home Assistant Integration
Version: 6.2 - Auto-reauth with fallback to exception
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
import base64
import time


import logging

_LOGGER = logging.getLogger(__name__)


class MySportsAuthError(Exception):
    """Exception raised when authentication fails permanently."""

    pass


class MySportsAPI:
    """API Wrapper for MySports Platform"""

    def __init__(self, username: str, password: str):
        """
        Initialize MySports API

        Args:
            username: MySports username/email
            password: MySports password
        """
        self.username = username
        self.password = password
        self.base_url = "https://www.mysports.com"
        self.session = requests.Session()

        # Setup Basic Auth
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode("ascii")
        base64_auth = base64.b64encode(auth_bytes).decode("ascii")

        # Browser headers required for API access
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Authorization": f"Basic {base64_auth}",
                "Content-Type": "application/json",
                "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "x-nox-client-type": "WEB",
                "x-nox-web-context": "utm_source=google&utm_medium=organic",
            }
        )

        # Session state
        self.is_authenticated = False
        self.session_expires_at = None
        self._request_retries = 3
        self._retry_delay = 1
        self._last_error = None

    def _make_request(
        self, method: str, url: str, **kwargs
    ) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            **kwargs: Additional requests arguments

        Returns:
            Response object or None if all retries fail
        """
        for attempt in range(self._request_retries):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)

                # Don't retry on client errors (except 401)
                if 400 <= response.status_code < 500 and response.status_code != 401:
                    return response

                # Retry on server errors or 401
                if response.status_code >= 500 or response.status_code == 401:
                    if attempt < self._request_retries - 1:
                        time.sleep(self._retry_delay * (attempt + 1))
                        continue

                return response

            except requests.RequestException as e:
                self._last_error = str(e)
                if attempt < self._request_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                    continue
                print(f"Request failed after {self._request_retries} attempts: {e}")
                return None

        return None

    def login(self) -> bool:
        """
        Perform login with Basic Auth

        Returns:
            bool: True if login successful
        """
        # Check existing session
        if self.is_authenticated and self.session_expires_at:
            if datetime.now() < self.session_expires_at:
                if self._check_session_valid():
                    return True

        # Perform login
        login_url = f"{self.base_url}/login"
        payload = {"username": self.username, "password": self.password}

        response = self._make_request("POST", login_url, json=payload)

        if not response or response.status_code != 200:
            status = response.status_code if response else "No response"
            print(f"Login failed: Status {status}")
            if response:
                print(f"Response: {response.text[:200]}")
            self._last_error = f"Login failed: {status}"
            self.is_authenticated = False
            return False

        self.is_authenticated = True
        self.session_expires_at = datetime.now() + timedelta(days=7)
        self._last_error = None
        return True

    def _check_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.is_authenticated:
            return False

        response = self._make_request("GET", f"{self.base_url}/v1/me/info")

        if not response:
            return False

        if response.status_code == 401:
            self.is_authenticated = False
            return False

        return response.status_code == 200

    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid session.
        Returns True if authenticated, False if permanent auth failure.

        Raises:
            MySportsAuthError: If authentication fails permanently (wrong credentials)
        """
        if self.is_authenticated and self.session_expires_at:
            if datetime.now() < self.session_expires_at and self._check_session_valid():
                return True

        # Try to login
        if not self.login():
            # Login failed - this means credentials are wrong
            raise MySportsAuthError("Invalid credentials")
        return True

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get user information

        Returns:
            Dict with user info or None on error

        Raises:
            MySportsAuthError: When authentication fails permanently
        """
        self._ensure_authenticated()

        response = self._make_request("GET", f"{self.base_url}/v1/me/info")

        if not response or response.status_code != 200:
            if response and response.status_code == 401:
                # Session expired after we thought it was valid
                self.is_authenticated = False
                self._ensure_authenticated()
                # Retry after reauth
                response = self._make_request("GET", f"{self.base_url}/v1/me/info")
            if not response or response.status_code != 200:
                print(
                    f"Failed to get user info: {response.status_code if response else 'No response'}"
                )
                return None

        return response.json() if response else None

    def get_studios(self) -> List[Dict[str, Any]]:
        """
        Get connected studios with logo URL

        Returns:
            List of studios with id, name, primary status, logo_url, etc.
        """
        user_info = self.get_user_info()
        if not user_info or "studioConnects" not in user_info:
            return []

        studios = []
        for studio in user_info["studioConnects"]:
            studio_info = {
                "id": studio.get("studioId"),
                "name": studio.get("studioName"),
                "primary": studio.get("primary", False),
                "tenant": studio.get("tenant"),
                "tracking_enabled": studio.get("trackingEnabled", False),
                "logo_url": None,
            }

            if studio.get("studioLogo") and "url" in studio["studioLogo"]:
                studio_info["logo_url"] = studio["studioLogo"]["url"]

            studios.append(studio_info)

        return studios

    def get_utilization(self, studio_id: int) -> Optional[int]:
        """
        Get active check-in count for a studio.
        Automatically re-authenticates if session expired.

        Args:
            studio_id: Studio ID

        Returns:
            Number of active people or None on error

        Raises:
            MySportsAuthError: When authentication fails permanently (wrong credentials)
        """
        # Ensure we have a valid session
        self._ensure_authenticated()

        endpoint = (
            f"{self.base_url}/nox/v1/studios/{studio_id}/utilization/v2/active-checkin"
        )
        response = self._make_request("GET", endpoint)

        if not response:
            return None

        # Session expired - try one more time with fresh authentication
        if response.status_code == 401:
            self.is_authenticated = False
            self._ensure_authenticated()  # This will raise MySportsAuthError if credentials wrong
            response = self._make_request("GET", endpoint)

        if not response or response.status_code != 200:
            if response and response.status_code != 401:
                print(f"Utilization query failed: {response.status_code}")
            return None

        try:
            data = response.json()
            if "value" in data:
                return data["value"]
            elif "activeCheckins" in data:
                return len(data["activeCheckins"])
            elif "count" in data:
                return data["count"]
            else:
                print(f"Unknown response format: {data.keys()}")
                return None
        except (KeyError, ValueError) as e:
            print(f"Failed to parse utilization data: {e}")
            return None

    def get_primary_studio_utilization(self) -> Optional[int]:
        """
        Get utilization for primary studio

        Returns:
            Number of active people or None
        """
        studios = self.get_studios()
        if not studios:
            print("No studios found")
            return None

        primary = next((s for s in studios if s.get("primary")), studios[0])
        print(f"Using studio: {primary['name']} (ID: {primary['id']})")
        return self.get_utilization(primary["id"])

    def get_all_studios_utilization(self) -> Dict[str, Any]:
        """
        Get utilization for all studios

        Returns:
            Dictionary with studio utilization data
        """
        studios = self.get_studios()
        results = {"timestamp": datetime.now().isoformat(), "studios": []}

        for studio in studios:
            utilization = self.get_utilization(studio["id"])
            results["studios"].append(
                {
                    "id": studio["id"],
                    "name": studio["name"],
                    "primary": studio["primary"],
                    "logo_url": studio.get("logo_url"),
                    "active_checkins": utilization if utilization is not None else -1,
                    "available": utilization is not None,
                }
            )

        return results

    def get_courses(
        self, start_date: datetime, end_date: datetime, organization_unit_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Fetch courses for given time range and organization units.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            organization_unit_ids: List of studio/organization unit IDs

        Returns:
            List of course objects as returned by the API
        """
        self._ensure_authenticated()

        # Format dates as YYYY-MM-DD
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Build URL with query parameters
        url = f"{self.base_url}/nox/v2/bookableitems/courses/with-canceled"
        params = {
            "startDate": start_str,
            "endDate": end_str,
            "employeeIds": "",  # Keep empty as not needed
            "organizationUnitIds": ",".join(str(uid) for uid in organization_unit_ids),
        }

        response = self._make_request("GET", url, params=params)

        if not response:
            _LOGGER.error("No response when fetching courses")
            return []

        if response.status_code == 401:
            # Session expired, re-authenticate and retry once
            self.is_authenticated = False
            self._ensure_authenticated()
            response = self._make_request("GET", url, params=params)
            if not response:
                return []

        if response.status_code != 200:
            _LOGGER.error("Failed to fetch courses: HTTP %s", response.status_code)
            return []

        try:
            data = response.json()
            if isinstance(data, list):
                return data
            else:
                _LOGGER.warning("Unexpected courses response format: %s", type(data))
                return []
        except ValueError as e:
            _LOGGER.error("Failed to parse courses JSON: %s", e)
            return []

    def logout(self) -> None:
        """Clear session and reset authentication"""
        self.session = requests.Session()
        self.is_authenticated = False
        self.session_expires_at = None
        self._last_error = None
