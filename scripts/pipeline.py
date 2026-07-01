"""Orchestrates a full pipeline run: scrape, diff, process, rebuild apps.json."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

from build_source import build_source
from process_app import (
    convert_icon_to_png,
    download_ipa,
    extract_bundle_info,
    sha256_and_size,
    upload_release_asset,
)
from scrape import scrape_tracked_apps

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "apps.yaml"
STATE_PATH = REPO_ROOT / "state" / "state.json"
ICONS_DIR = REPO_ROOT / "icons"
APPS_JSON_PATH = REPO_ROOT / "apps.json"
GITHUB_REPO = "MountainofPenguin/moe-altstore"


def load_config() -> list[dict]:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)["apps"]


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def apps_needing_processing(config_apps: list[dict], scraped: dict, state: dict) -> list[dict]:
    """Return config entries whose scraped data_modified differs from cached state."""
    needing = []
    for app_config in config_apps:
        card = scraped.get(app_config["app_id"])
        if card is None:
            continue
        cached = state.get(app_config["slug"])
        if cached is None or cached.get("data_modified") != card.data_modified:
            needing.append(app_config)
    return needing


def process_single_app(app_config: dict, card, tmp_dir: Path) -> dict:
    """Download, inspect, and re-host one app's IPA. Returns a new state entry."""
    ipa_path = tmp_dir / f"{app_config['slug']}.ipa"
    download_ipa(card, ipa_path)

    bundle_identifier, plist_version = extract_bundle_info(ipa_path)
    sha256, size = sha256_and_size(ipa_path)

    icon_response = requests.get(card.icon_url, timeout=30)
    icon_response.raise_for_status()
    png_bytes = convert_icon_to_png(icon_response.content)
    icon_path = ICONS_DIR / f"{app_config['slug']}.png"
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    icon_path.write_bytes(png_bytes)

    tag = f"{app_config['slug']}-{plist_version}"
    download_url = upload_release_asset(GITHUB_REPO, tag, ipa_path, app_config["name"])

    version_entry = {
        "version": plist_version,
        "date": datetime.fromtimestamp(card.data_modified, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "description": card.changelog or card.description,
        "download_url": download_url,
        "size": size,
        "sha256": sha256,
    }

    return {
        "app_id": card.app_id,
        "data_modified": card.data_modified,
        "bundle_identifier": bundle_identifier,
        "description": card.description,
        "icon_url": f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/icons/{app_config['slug']}.png",
        "version_entry": version_entry,
    }


def run() -> None:
    config_apps = load_config()
    state = load_state()

    tracked_ids = {c["app_id"] for c in config_apps}
    scraped = scrape_tracked_apps(tracked_ids)

    to_process = apps_needing_processing(config_apps, scraped, state)
    print(f"{len(to_process)} app(s) need processing: {[c['slug'] for c in to_process]}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for app_config in to_process:
            slug = app_config["slug"]
            card = scraped[app_config["app_id"]]
            try:
                result = process_single_app(app_config, card, tmp_dir)
            except Exception as exc:  # noqa: BLE001 - per-app isolation is required here
                print(f"::warning::Failed to process {slug}: {exc}")
                continue

            existing_versions = state.get(slug, {}).get("versions", [])
            new_version = result["version_entry"]
            versions = [v for v in existing_versions if v["version"] != new_version["version"]]
            versions.append(new_version)
            versions = versions[-5:]  # keep the last 5 versions of history

            state[slug] = {
                "app_id": result["app_id"],
                "data_modified": result["data_modified"],
                "bundle_identifier": result["bundle_identifier"],
                "description": result["description"],
                "icon_url": result["icon_url"],
                "versions": versions,
            }
            save_state(state)  # persist after every app so partial progress isn't lost

    source = build_source(config_apps, state)
    APPS_JSON_PATH.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    run()
