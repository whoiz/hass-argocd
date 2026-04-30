"""ArgoCD API client."""

import logging
from typing import Any, Dict, List

import httpx

from .const import DOMAIN

_LOGGER = logging.getLogger(__package__)


class ArgoCDApiClient:
    """Define the ArgoCD API client."""

    def __init__(self, url: str, token: str, verify_ssl: bool) -> None:
        """Initialize the client."""
        self._url = url.rstrip("/")
        self._token = token
            self._verify_ssl = verify_ssl
        self._client = httpx.AsyncClient(
            base_url=self._url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            verify=self._verify_ssl,
        )
        )

    async def get_applications(self) -> List[Dict[str, Any]]:
        """Get all applications from ArgoCD."""
        try:
            resp = await self._client.get("/api/v1/applications")
            resp.raise_for_status()
            data = resp.json()
            return data.get("items", [])
        except httpx.HTTPError as exc:
            _LOGGER.error("Error fetching applications: %s", exc)
            return []

    async def get_application(self, name: str) -> Dict[str, Any]:
        """Get a specific application by name."""
        try:
            resp = await self._client.get(f"/api/v1/applications/{name}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            _LOGGER.error("Error fetching application %s: %s", name, exc)
            return {}

    async def sync_application(self, name: str) -> bool:
        """Sync an application."""
        try:
            resp = await self._client.post(
                f"/api/v1/applications/{name}/sync", json={}
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            _LOGGER.error("Error syncing application %s: %s", name, exc)
            return False

    async def close(self) -> None:
        """Close the client."""
        await self._client.aclose()