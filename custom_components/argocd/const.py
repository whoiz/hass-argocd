"""Constants for the ArgoCD integration."""

DOMAIN = "argocd"
DEFAULT_NAME = "ArgoCD"
DEFAULT_SCAN_INTERVAL = 60  # seconds

# Configuration keys
CONF_URL = "url"
CONF_TOKEN = "token"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_VERIFY_SSL = "verify_ssl"

# Attributes
ATTR_LAST_SYNC = "last_sync"
ATTR_HEALTH_STATUS = "health_status"
ATTR_SYNC_STATUS = "sync_status"
ATTR_REVISION = "revision"
ATTR_APPLICATION_NAME = "application_name"
ATTR_EXTERNAL_URLS = "external_urls"
ATTR_POD_NAME = "pod_name"
ATTR_NAMESPACE = "namespace"

# Sensor types
SENSOR_TYPES = {
    "sync_status": {
        "name": "Sync Status",
        "icon": "mdi:arrows-clockwise",
    },
    "health_status": {
        "name": "Health Status",
        "icon": "mdi:heart-pulse",
    },
    "last_sync": {
        "name": "Last Sync",
        "icon": "mdi:history",
    },
    "revision": {
        "name": "Revision",
        "icon": "mdi:git",
    },
    "external_urls": {
        "name": "External URLs",
        "icon": "mdi:web",
    },
}

# Service names
SERVICE_SYNC_APP = "sync_app"
SERVICE_DELETE_POD = "delete_pod"