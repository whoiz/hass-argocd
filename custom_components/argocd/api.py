"""ArgoCD API client."""

import asyncio
import logging
import ssl
from typing import Any, Dict, List, Union

import httpx

from .const import DOMAIN

_LOGGER = logging.getLogger(__package__)


class ArgoCDApiClient:
    """Define the ArgoCD API client."""

    def __init__(self, url: str, token: str, ssl_context: Union[ssl.SSLContext, bool]) -> None:
        """Initialize the client.

        ssl_context must be an ssl.SSLContext or False — never True,
        to avoid blocking SSL loading inside the event loop.
        """
        self._url = url.rstrip("/")
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=self._url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            verify=ssl_context,
        )

    @classmethod
    async def create(
        cls, url: str, token: str, verify_ssl: bool
    ) -> "ArgoCDApiClient":
        """Async factory: loads SSL context off the event loop when needed."""
        if verify_ssl:
            loop = asyncio.get_running_loop()
            ssl_context = await loop.run_in_executor(
                None, ssl.create_default_context
            )
        else:
            ssl_context = False
        return cls(url, token, ssl_context)

    async def get_applications(self) -> List[Dict[str, Any]]:
        """Get all applications from ArgoCD."""
        try:
            resp = await self._client.get("/api/v1/applications")
            resp.raise_for_status()
            data = resp.json()

            _LOGGER.debug(
                "ArgoCD API response: status=%s, type=%s, keys=%s",
                resp.status_code,
                type(data).__name__,
                list(data.keys()) if isinstance(data, dict) else "N/A",
            )

            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                items = data.get("items")
                _LOGGER.debug(
                    "ArgoCD items field: type=%s len=%s first_app=%s",
                    type(items).__name__,
                    len(items) if isinstance(items, list) else "N/A",
                    items[0].get("metadata", {}).get("name") if items else "N/A",
                )
                return items if isinstance(items, list) else []
            _LOGGER.warning("Unexpected API response type: %s", type(data).__name__)
            return []
        except httpx.HTTPError as exc:
            _LOGGER.error("Error fetching applications: %s", exc)
            return []
        except Exception as exc:
            _LOGGER.error("Unexpected error fetching applications: %s", exc)
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

    async def get_resource_tree(self, name: str) -> Dict[str, Any]:
        """Get the resource tree for a specific application."""
        try:
            resp = await self._client.get(f"/api/v1/applications/{name}/resource-tree")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            _LOGGER.error("Error fetching resource tree for %s: %s", name, exc)
            return {"nodes": []}

    async def delete_resource(
        self,
        app_name: str,
        kind: str,
        resource_name: str,
        namespace: str,
        version: str,
        group: str | None = None,
    ) -> bool:
        """Delete a resource (e.g. a Pod) within an application."""
        params: Dict[str, str] = {
            "kind": kind,
            "resourceName": resource_name,
            "namespace": namespace,
            "version": version,
        }
        if group:
            params["group"] = group
        try:
            resp = await self._client.delete(
                f"/api/v1/applications/{app_name}/resource", params=params
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            _LOGGER.error(
                "Error deleting resource %s/%s in app %s: %s",
                namespace,
                resource_name,
                app_name,
                exc,
            )
            return False

    async def get_pod_logs(
        self,
        app_name: str,
        pod_name: str,
        namespace: str,
        container: str | None = None,
        tail_lines: int = 100,
    ) -> str:
        """Get logs from a pod within an application."""
        params: Dict[str, str] = {
            "namespace": namespace,
            "kind": "Pod",
            "resourceName": pod_name,
            "tailLines": str(tail_lines),
        }
        if container:
            params["container"] = container
        try:
            resp = await self._client.get(
                f"/api/v1/applications/{app_name}/logs", params=params
            )
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as exc:
            _LOGGER.error(
                "Error fetching logs for pod %s/%s in app %s: %s",
                namespace,
                pod_name,
                app_name,
                exc,
            )
            return ""

    async def close(self) -> None:
        """Close the client."""
        await self._client.aclose()