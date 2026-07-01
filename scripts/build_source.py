"""Render apps.json from state.json + config/apps.yaml. Pure, deterministic."""
from __future__ import annotations

SOURCE_NAME = "Moe AltStore"
SOURCE_IDENTIFIER = "com.mountainofpenguin.moealtstore"
SOURCE_API_VERSION = "v2"
SOURCE_SUBTITLE = "Automated mirror of moe.mohkg1017.pro app mods"
SOURCE_DESCRIPTION = (
    "Scraped and re-hosted daily — apps are re-downloaded and republished "
    "whenever a new version appears on the source site."
)
SOURCE_ICON_URL = (
    "https://raw.githubusercontent.com/MountainofPenguin/moe-altstore/main/icons/moe_icon.png"
)
SOURCE_WEBSITE = "https://github.com/MountainofPenguin/moe-altstore"


def build_source(config_apps: list[dict], state: dict) -> dict:
    """Build the AltStore source dict from tracked-app config and processed state.

    config_apps: list of {app_id, slug, name, subtitle} from config/apps.yaml.
    state: dict keyed by slug, each value holding bundle_identifier,
        icon_url, description, and a versions list (each with version,
        date, description, download_url, size, min_os_version), as written
        by process_app.py.
    Apps with no state entry yet (never successfully processed) are omitted
    from the output rather than included with empty fields.
    """
    apps = []
    for app_config in config_apps:
        app_state = state.get(app_config["slug"])
        if not app_state or not app_state.get("versions"):
            continue
        apps.append(
            {
                "name": app_config["name"],
                "bundleIdentifier": app_state["bundle_identifier"],
                "developerName": "Moe Apps",
                "subtitle": app_config["subtitle"],
                "localizedDescription": app_state["description"],
                "iconURL": app_state["icon_url"],
                "screenshots": [],
                "versions": [
                    {
                        "version": v["version"],
                        "date": v["date"],
                        "localizedDescription": v["description"],
                        "downloadURL": v["download_url"],
                        "size": v["size"],
                        "minOSVersion": v["min_os_version"],
                    }
                    for v in app_state["versions"]
                ],
                "appPermissions": {"entitlements": [], "privacy": {}},
            }
        )
    return {
        "name": SOURCE_NAME,
        "identifier": SOURCE_IDENTIFIER,
        "apiVersion": SOURCE_API_VERSION,
        "subtitle": SOURCE_SUBTITLE,
        "description": SOURCE_DESCRIPTION,
        "iconURL": SOURCE_ICON_URL,
        "website": SOURCE_WEBSITE,
        "apps": apps,
        "news": [],
    }
