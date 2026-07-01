"""Scrape moe.mohkg1017.pro's app grid and extract cards for tracked apps."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://moe.mohkg1017.pro"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)
NUM_PAGES = 11
PAGE_DELAY_SECONDS = 1.5


@dataclass
class AppCard:
    app_id: str
    name: str
    data_modified: int
    icon_url: str
    description: str
    changelog: str | None
    version_text: str
    size_text: str
    drive_file_id: str
    download_url: str


def extract_drive_file_id(url: str) -> str | None:
    """Extract a Google Drive file ID from any of the site's URL shapes.

    Handles `uc?id=<ID>&export=download`, `open?id=<ID>&usp=drive_fs`,
    and `file/d/<ID>/view?usp=...`. Returns None for non-Drive URLs.
    """
    if "drive.google.com" not in url:
        return None
    query_id = parse_qs(urlparse(url).query).get("id")
    if query_id:
        return query_id[0]
    path_match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if path_match:
        return path_match.group(1)
    return None
