"""Render apps.json from state.json + config/apps.yaml. Pure, deterministic."""
from __future__ import annotations

import re

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

_VERSION_TOKEN_RE = re.compile(r"\d+(?:\.\d+)+")


def compose_version(base_version: str, display_name: str | None) -> str:
    """Combine the base app version with the tweak/build version from the site name.

    The source site's listing name (e.g. "Youtube 21.28.3 Moe Multi 10.16 Not
    Stable") embeds the modder's own build version ("10.16") after the base app
    version ("21.28.3"). The base version comes from the IPA's Info.plist and is
    all AltStore would otherwise show, which both hides which tweak build the user
    is getting and stays identical when the modder ships a new build for the same
    base app version (so no update registers). Surfacing "21.28.3 (10.16)" fixes
    both: the tweak version is visible, and it changes on every tweak-only update.

    The tweak version is taken as the last dotted-numeric token in the name that
    differs from the base version. If none is found (e.g. "Webssh 32.1 Pro"), the
    base version is returned unchanged.
    """
    tokens = _VERSION_TOKEN_RE.findall(display_name or "")
    for token in reversed(tokens):
        if token != base_version:
            return f"{base_version} ({token})"
    return base_version


def build_source(config_apps: list[dict], state: dict) -> dict:
    """Build the AltStore source dict from tracked-app config and processed state.

    config_apps: list of {app_id, slug, name, subtitle} from config/apps.yaml.
    state: dict keyed by slug, each value holding bundle_identifier, icon_url,
        description, and a versions list. Each version entry holds version (the
        base app version), display_name (the full site listing name at process
        time), data_modified (the site's epoch update timestamp, used to sort),
        date, description, download_url, size, min_os_version.
    Apps with no state entry yet (never successfully processed) are omitted from
    the output rather than included with empty fields. Each app's versions are
    emitted newest-first (AltStore/SideStore treat versions[0] as current), and
    each version's emitted version string is the base version composed with the
    tweak version parsed from that entry's display_name.
    """
    apps = []
    for app_config in config_apps:
        app_state = state.get(app_config["slug"])
        if not app_state or not app_state.get("versions"):
            continue
        sorted_versions = sorted(
            app_state["versions"],
            key=lambda v: v.get("data_modified", 0),
            reverse=True,
        )
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
                        "version": compose_version(v["version"], v.get("display_name")),
                        "date": v["date"],
                        "localizedDescription": v["description"],
                        "downloadURL": v["download_url"],
                        "size": v["size"],
                        "minOSVersion": v["min_os_version"],
                    }
                    for v in sorted_versions
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
