"""Scrape moe.mohkg1017.pro's app grid and extract cards for tracked apps."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, parse_qs

from curl_cffi import requests
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


def parse_app_cards(html: str) -> list[AppCard]:
    """Parse every app-card article on one grid page."""
    soup = BeautifulSoup(html, "html.parser")
    cards = []
    for article in soup.select("article.app-card"):
        open_link = article.select_one("a.app-card-open-link")
        if open_link is None:
            continue
        id_match = re.search(r"/app/(app_\d+_\d+)", open_link["href"])
        if id_match is None:
            continue

        download_link = article.select_one("a.download-link")
        if download_link is None:
            continue

        try:
            download_url = download_link["href"]

            icon_img = article.select_one(".app-icon img")
            icon_url = urljoin(BASE_URL, icon_img["src"]) if icon_img else ""

            description_el = article.select_one("p.app-description")
            description = description_el.get_text(strip=True) if description_el else ""

            changelog_el = article.select_one(".app-changelog-preview .changelog-text")
            changelog = changelog_el.get_text(strip=True) if changelog_el else None

            meta_spans = article.select(".app-meta-row span")
            version_text = meta_spans[0].get_text(strip=True) if len(meta_spans) > 0 else ""
            size_text = meta_spans[1].get_text(strip=True) if len(meta_spans) > 1 else ""

            cards.append(
                AppCard(
                    app_id=id_match.group(1),
                    name=article["data-name"],
                    data_modified=int(article["data-modified"]),
                    icon_url=icon_url,
                    description=description,
                    changelog=changelog,
                    version_text=version_text,
                    size_text=size_text,
                    drive_file_id=extract_drive_file_id(download_url) or "",
                    download_url=download_url,
                )
            )
        except (KeyError, ValueError):
            continue
    return cards


def fetch_page(session: requests.Session, page: int) -> str:
    response = session.get(f"{BASE_URL}/", params={"page": page}, timeout=30)
    response.raise_for_status()
    return response.text


def scrape_tracked_apps(tracked_ids: set[str]) -> dict[str, AppCard]:
    """Scan all grid pages, return the latest card for every tracked app_id found."""
    session = requests.Session(impersonate="chrome")
    session.headers["User-Agent"] = USER_AGENT

    found: dict[str, AppCard] = {}
    for page in range(1, NUM_PAGES + 1):
        html = fetch_page(session, page)
        for card in parse_app_cards(html):
            if card.app_id in tracked_ids:
                found[card.app_id] = card
        if page < NUM_PAGES:
            time.sleep(PAGE_DELAY_SECONDS)
    return found
