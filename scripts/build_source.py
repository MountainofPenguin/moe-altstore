"""Render apps.json from state.json + config/apps.yaml. Pure, deterministic."""
from __future__ import annotations

SOURCE_NAME = "Moe AltStore"
SOURCE_IDENTIFIER = "com.mountainofpenguin.moealtstore"


def build_source(config_apps: list[dict], state: dict) -> dict:
    """Build the AltStore source dict from tracked-app config and processed state.

    config_apps: list of {app_id, slug, name, subtitle} from config/apps.yaml.
    state: dict keyed by slug, each value holding bundle_identifier,
        icon_url, description, and a versions list (each with version,
        date, description, download_url, size), as written by process_app.py.
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
                "versions": [
                    {
                        "version": v["version"],
                        "date": v["date"],
                        "localizedDescription": v["description"],
                        "downloadURL": v["download_url"],
                        "size": v["size"],
                    }
                    for v in app_state["versions"]
                ],
            }
        )
    return {
        "name": SOURCE_NAME,
        "identifier": SOURCE_IDENTIFIER,
        "apps": apps,
    }
