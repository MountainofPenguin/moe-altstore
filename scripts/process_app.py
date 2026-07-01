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


def convert_icon_to_png(icon_bytes: bytes) -> bytes:
    """Re-encode an icon (webp or otherwise) as PNG bytes."""
    image = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def choose_downloader(download_url: str) -> str:
    """Return 'gdown' for Google Drive URLs, 'requests' for anything else."""
    if "drive.google.com" in download_url:
        return "gdown"
    return "requests"


def download_via_gdown(file_id: str, dest_path: Path) -> None:
    import gdown

    gdown.download(f"https://drive.google.com/uc?id={file_id}", str(dest_path), quiet=True)


def download_via_requests(url: str, dest_path: Path) -> None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        )
    }
    with requests.get(url, stream=True, timeout=60, headers=headers) as response:
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)


def download_ipa(card, dest_path: Path) -> None:
    """Download an app's IPA, routing to the right downloader for its host."""
    if choose_downloader(card.download_url) == "gdown":
        download_via_gdown(card.drive_file_id, dest_path)
    else:
        download_via_requests(card.download_url, dest_path)


def upload_release_asset(repo: str, tag: str, asset_path: Path, title: str) -> str:
    """Create (if needed) a GitHub release and upload the IPA as its asset.

    Returns the public download URL for the uploaded asset. Safe to call
    repeatedly for the same tag (idempotent: reuses the release, replaces
    the asset with --clobber).
    """
    view = subprocess.run(
        ["gh", "release", "view", tag, "--repo", repo],
        capture_output=True,
        text=True,
    )
    if view.returncode != 0:
        subprocess.run(
            [
                "gh", "release", "create", tag,
                "--repo", repo,
                "--title", title,
                "--notes", f"Automated build for {title}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    subprocess.run(
        ["gh", "release", "upload", tag, str(asset_path), "--repo", repo, "--clobber"],
        check=True,
        capture_output=True,
        text=True,
    )
    return f"https://github.com/{repo}/releases/download/{tag}/{asset_path.name}"
