"""Download, inspect, and re-host a single app's IPA."""
from __future__ import annotations

import hashlib
import io
import plistlib
import subprocess
import zipfile
from pathlib import Path

import requests
from PIL import Image


def sha256_and_size(file_path: Path) -> tuple[str, int]:
    """Compute the sha256 hex digest and byte size of a file."""
    hasher = hashlib.sha256()
    size = 0
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
            size += len(chunk)
    return hasher.hexdigest(), size


def extract_bundle_info(ipa_path: Path) -> tuple[str, str]:
    """Read CFBundleIdentifier and CFBundleShortVersionString from an .ipa."""
    with zipfile.ZipFile(ipa_path) as ipa:
        info_plist_names = [
            name
            for name in ipa.namelist()
            if name.startswith("Payload/")
            and name.endswith(".app/Info.plist")
            and name.count("/") == 2
        ]
        if not info_plist_names:
            raise ValueError(f"No top-level Info.plist found in {ipa_path}")
        plist_bytes = ipa.read(info_plist_names[0])
    plist = plistlib.loads(plist_bytes)
    return plist["CFBundleIdentifier"], plist["CFBundleShortVersionString"]
