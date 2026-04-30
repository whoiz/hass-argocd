# HomeAssistant ArgoCD Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Integrate ArgoCD applications into HomeAssistant as entities, monitor their status, and trigger manual synchronizations.

## Features

*   **Application Sensors**: Each ArgoCD application is exposed as a sensor entity in HomeAssistant, displaying:
    *   **Sync Status**: `Synced`, `OutOfSync`, etc.
    *   **Health Status**: `Healthy`, `Degraded`, `Missing`, etc.
    *   **Last Sync**: Timestamp of the last successful synchronization.
    *   **Revision**: The currently deployed Git revision.
*   **Synchronization Buttons**: A dedicated button entity for each application allows you to manually trigger a synchronization directly from HomeAssistant.
*   **UI Configuration**: Easy setup through the HomeAssistant UI.

## Installation

### Via HACS (Recommended)

1.  Open HACS in your HomeAssistant instance.
2.  Go to "Integrations".
3.  Click on the three dots in the top right corner and select "Custom repositories".
4.  Add the following URL as a "Integration" type:
    `https://github.com/whoiz/hass-argocd.git`
5.  Search for "ArgoCD" in HACS and install it.
6.  Restart HomeAssistant.

### Manual Installation

1.  Download the latest release from the [GitHub repository](https://github.com/whoiz/hass-argocd/releases).
2.  Unpack the `argocd` folder into your HomeAssistant `custom_components` directory.
    Your path should look like: `<config_dir>/custom_components/argocd/`.
3.  Restart HomeAssistant.

## Creating an ArgoCD API Token

To allow HomeAssistant to communicate with your ArgoCD instance, you need to create a dedicated API token.

1.  **Log in to ArgoCD**: Access your ArgoCD UI.
2.  **Navigate to User Info**: Click on your username in the sidebar or top right corner, then select "User Info".
3.  **Generate New Token**: In the "Tokens" section, click "Generate New Token".
    *   **Expiration**: Set an appropriate expiration date (e.g., "Never" for persistent integration, or a reasonable timeframe for security).
    *   **Applications (Optional but Recommended)**: For security best practices, you can restrict the token to specific applications if you only want to monitor a subset.
4.  **Copy Token**: Copy the generated token immediately. It will only be shown once.

## Configuration

After installation and HomeAssistant restart:

1.  Go to "Settings" -> "Devices & Services".
2.  Click the "ADD INTEGRATION" button.
3.  Search for "ArgoCD" and select it.
4.  Enter the following details:
    *   **ArgoCD URL**: The full URL to your ArgoCD instance (e.g., `https://argocd.example.com`).
    *   **Access Token**: The API token you generated in ArgoCD.
    *   **Scan Interval (optional)**: How often (in seconds) HomeAssistant should check for updates. Default is 60 seconds.

## Entities

For each ArgoCD application, the integration will create the following entities:

*   **Sensor Entity**:
    *   `sensor.your_app_name_sync_status`
    *   `sensor.your_app_name_health_status`
    *   `sensor.your_app_name_last_sync`
    *   `sensor.your_app_name_revision`
*   **Button Entity**:
    *   `button.your_app_name_sync`

## Services

A service is available for triggering application synchronizations through automations:

*   `argocd.sync_app`:
    *   `application_name` (required): The name of the ArgoCD application to synchronize.

    **Example Automation (YAML):**

    ```yaml
    alias: Sync My App Nightly
    description: ''
    trigger:
      - platform: time
        at: '03:00:00'
    condition: []
    action:
      - service: argocd.sync_app
        data:
          application_name: my-important-app
    mode: single
    ```

## Example Lovelace Dashboard Configuration

Here's an example of how you can display your ArgoCD applications in a Lovelace dashboard:

```yaml
type: entities
entities:
  - type: custom:multiple-entity-row
    entity: sensor.my_app_sync_status
    name: My Application
    secondary_info: last-changed
    entities:
      - entity: sensor.my_app_health_status
        name: Health
      - entity: sensor.my_app_last_sync
        name: Last Sync
  - type: button
    entity: button.my_app_sync
    name: Sync My Application
    icon: mdi:arrows-clockwise
  - type: divider
```

## Support

For issues, feature requests, or questions, please visit the [issue tracker](https://github.com/whoiz/hass-argocd/issues) on GitHub.
