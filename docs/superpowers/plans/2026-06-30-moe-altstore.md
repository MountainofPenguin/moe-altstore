# Moe AltStore Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `moe-altstore` repo — a daily-automated scraper/pipeline that tracks 37 apps on moe.mohkg1017.pro, re-hosts their IPAs on GitHub Releases, and generates an AltStore-compatible `apps.json`.

**Architecture:** Four small Python modules (`scrape.py`, `process_app.py`, `build_source.py`, `pipeline.py`) each with one job, driven by a GitHub Actions daily cron. `config/apps.yaml` is the human-editable list of tracked apps (keyed by the site's stable per-listing ID); `state/state.json` is the pipeline's own cache of what's already been processed; `apps.json` is regenerated from `state.json` on every run, never hand-edited.

**Tech Stack:** Python 3.12, `requests` + `beautifulsoup4` (scraping), `gdown` (Google Drive large-file downloads), `Pillow` (icon conversion), `PyYAML` (config), `gh` CLI (GitHub Releases), `pytest` (tests). Spec: `docs/superpowers/specs/2026-06-30-moe-altstore-design.md`.

---

## Task 1: Repo scaffolding

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `tests/conftest.py`
- Create: `README.md`
- Create: `icons/.gitkeep`

- [ ] **Step 1: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
venv/
*.ipa
.pytest_cache/
.DS_Store
```

- [ ] **Step 2: Create `requirements.txt`**

```
requests>=2.31,<3
beautifulsoup4>=4.12,<5
gdown>=5.2,<6
Pillow>=10.4,<11
PyYAML>=6.0,<7
```

- [ ] **Step 3: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest>=8.0,<9
```

- [ ] **Step 4: Create `tests/conftest.py`** (puts `scripts/` on the import path for every test file, so tests can do `import scrape` instead of repeating `sys.path` hacks)

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
```

- [ ] **Step 5: Create a `README.md` stub** (expanded fully in Task 13)

```markdown
# Moe AltStore

An AltStore/SideStore source that mirrors a curated set of apps from
moe.mohkg1017.pro, kept in sync by a daily GitHub Actions job.

Setup and usage docs are being written — see
`docs/superpowers/specs/2026-06-30-moe-altstore-design.md` for the design
in the meantime.
```

- [ ] **Step 6: Create `icons/.gitkeep`** (empty file, so git tracks the otherwise-empty `icons/` directory until the pipeline commits real icons into it)

```

```

- [ ] **Step 7: Install dev dependencies**

Run: `cd "/Users/schwe/Downloads/Claude Projects/Moe Source" && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`
Expected: all packages install without error.

- [ ] **Step 8: Commit**

```bash
cd "/Users/schwe/Downloads/Claude Projects/Moe Source"
git add .gitignore requirements.txt requirements-dev.txt tests/conftest.py README.md icons/.gitkeep
git commit -m "Scaffold repo: gitignore, deps, test config, README stub"
```

---

## Task 2: Tracked-apps config

**Files:**
- Create: `config/apps.yaml`

- [ ] **Step 1: Write the full tracked-apps list** (all 37 apps resolved during design, keyed by the site's stable `app_id`)

```yaml
# Tracked apps: stable site app_id -> repo metadata.
# To add or remove a tracked app, edit this file only — no code changes needed.
# Find an app's app_id from its "Details" link on moe.mohkg1017.pro
# (the URL looks like /app/app_1757018667_5902).
apps:
  - app_id: app_1758405429_2536
    slug: carrot
    name: "Carrot"
    subtitle: "Weather app, Moe Pro patch"

  - app_id: app_1757008016_7340
    slug: webssh
    name: "Webssh"
    subtitle: "SSH client, Pro patch"

  - app_id: app_1769231115_3988
    slug: moereddit
    name: "MoeReddit"
    subtitle: "Reddit client, MoeReddit build"

  - app_id: app_1776873562_1009
    slug: infuse-moe-plus
    name: "Infuse (Moe Plus)"
    subtitle: "Media player, Moe Plus patch"

  - app_id: app_1757008016_2941
    slug: infuse-plus-2-5
    name: "Infuse (Plus 2.5)"
    subtitle: "Media player, Plus 2.5 patch"

  - app_id: app_1757018667_5902
    slug: youtube-moe-multi
    name: "YouTube (Moe Multi)"
    subtitle: "Multi-tweak loader: YTKillerPlus, DLTube, TubeLRD, YTLite, and more"

  - app_id: app_1757017627_3645
    slug: youtube-moe-ytk
    name: "YouTube (Moe YTK)"
    subtitle: "YTKillerPlus tweak build"

  - app_id: app_1757008016_5162
    slug: youtube-ytplus-cyan
    name: "YouTube (YTPlus Cyan Edition)"
    subtitle: "YTPlus tweak build, Cyan Edition"

  - app_id: app_1757017764_8118
    slug: youtube-lrd
    name: "YouTube (LRD)"
    subtitle: "TubeLRD tweak build"

  - app_id: app_1757018539_5457
    slug: youtube-dltube-patched
    name: "YouTube (DLTube, Moe Patched)"
    subtitle: "DLTube tweak build"

  - app_id: app_1767418206_7299
    slug: youtube-dltube-cracked
    name: "YouTube (Moe DLTube, Cracked)"
    subtitle: "DLTube tweak build, cracked"

  - app_id: app_1767418254_3524
    slug: youtube-lrd-cracked
    name: "YouTube (Moe LRD, Cracked)"
    subtitle: "TubeLRD tweak build, cracked"

  - app_id: app_1759517364_7181
    slug: youtube-moe-sy
    name: "YouTube (Moe SY)"
    subtitle: "SY tweak build"

  - app_id: app_1757008016_9593
    slug: youtube-ytplus-temp-free
    name: "YouTube (Moe YTPlus, Temp Free)"
    subtitle: "YTPlus tweak build"

  - app_id: app_1770927442_3128
    slug: youtube-music
    name: "YouTube Music"
    subtitle: "Ultimate Enhanced tweak build"

  - app_id: app_1757008016_9180
    slug: instagram-moe-multi
    name: "Instagram (Moe Multi)"
    subtitle: "Multi-tweak loader"

  - app_id: app_1757008016_2176
    slug: instagram-sy
    name: "Instagram (SY)"
    subtitle: "SY tweak build"

  - app_id: app_1757008016_6988
    slug: instagram-dl
    name: "Instagram (DL)"
    subtitle: "DL tweak build"

  - app_id: app_1757008016_8064
    slug: instagram-lrd
    name: "Instagram (LRD)"
    subtitle: "LRD tweak build"

  - app_id: app_1757008016_8023
    slug: instagram-ac
    name: "Instagram (AC)"
    subtitle: "AC tweak build"

  - app_id: app_1757008016_5831
    slug: instagram-bh
    name: "Instagram (BH)"
    subtitle: "BH tweak build"

  - app_id: app_1767395377_5704
    slug: instagram-dl-cracked
    name: "Instagram (DL, Cracked)"
    subtitle: "DL tweak build, cracked"

  - app_id: app_1757008016_2103
    slug: instagram-igformat
    name: "Instagram (IGFormat)"
    subtitle: "IGFormat tweak build"

  - app_id: app_1757008016_8735
    slug: instagram-ink-plus
    name: "Instagram (INK Plus)"
    subtitle: "INK Plus tweak build"

  - app_id: app_1767395338_6014
    slug: instagram-lrd-cracked
    name: "Instagram (LRD, Cracked)"
    subtitle: "LRD tweak build, cracked"

  - app_id: app_1776979936_3686
    slug: instagram-ryukgram
    name: "Instagram (Moe RyukGram)"
    subtitle: "RyukGram tweak build"

  - app_id: app_1767805749_5206
    slug: instagram-nyx-b2-cracked
    name: "Instagram (NYX B2, Cracked)"
    subtitle: "NYX tweak build, cracked"

  - app_id: app_1757008016_8129
    slug: instagram-nyx-b4
    name: "Instagram (NYX B4)"
    subtitle: "NYX tweak build"

  - app_id: app_1770262907_3468
    slug: instagram-regram
    name: "Instagram (Regram)"
    subtitle: "Regram OLED tweak build"

  - app_id: app_1757008016_8648
    slug: instagram-rocket-cracked
    name: "Instagram (Rocket, Cracked)"
    subtitle: "Rocket tweak build, cracked"

  - app_id: app_1758659552_5935
    slug: instagram-sc
    name: "Instagram (SC)"
    subtitle: "SC tweak build"

  - app_id: app_1757008016_6127
    slug: instagram-theta
    name: "Instagram (Theta)"
    subtitle: "Theta tweak build"

  - app_id: app_1757008016_1558
    slug: twitch-bare
    name: "Twitch"
    subtitle: "Standard build"

  - app_id: app_1768431327_4203
    slug: twitch-adfree
    name: "Twitch (Adfree, Moe Control)"
    subtitle: "Adfree tweak build"

  - app_id: app_1776406804_3230
    slug: twitch-tweach
    name: "Twitch (Tweach)"
    subtitle: "Tweach tweak build"

  - app_id: app_1776873777_5494
    slug: twitch-twitchcontrol
    name: "Twitch (Moe TwitchControl)"
    subtitle: "TwitchControl tweak build"

  - app_id: app_1776873611_4164
    slug: twitchv-tweach
    name: "Twitch (Twitchv, Moe Tweach)"
    subtitle: "Tweach tweak build"
```

- [ ] **Step 2: Verify it parses and has 37 entries**

Run: `cd "/Users/schwe/Downloads/Claude Projects/Moe Source" && .venv/bin/python3 -c "import yaml; apps = yaml.safe_load(open('config/apps.yaml'))['apps']; print(len(apps)); assert len(apps) == 37; assert len({a['slug'] for a in apps}) == 37; assert len({a['app_id'] for a in apps}) == 37"`
Expected: prints `37`, no assertion error.

- [ ] **Step 3: Commit**

```bash
git add config/apps.yaml
git commit -m "Add config/apps.yaml: the 37 tracked apps"
```

---

## Task 3: `scrape.py` — Google Drive URL parsing

**Files:**
- Create: `scripts/scrape.py`
- Test: `tests/test_scrape.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_scrape.py
import scrape


def test_extract_drive_file_id_uc_query_format():
    url = "https://drive.google.com/uc?id=1eigsUQ10jGGhUyV658Vw6wUO8mZC9ej_&export=download"
    assert scrape.extract_drive_file_id(url) == "1eigsUQ10jGGhUyV658Vw6wUO8mZC9ej_"


def test_extract_drive_file_id_open_query_format():
    url = "https://drive.google.com/open?id=1Ik0i3j-apPlTITfnMMyA0CmEfjbKOqrE&usp=drive_fs"
    assert scrape.extract_drive_file_id(url) == "1Ik0i3j-apPlTITfnMMyA0CmEfjbKOqrE"


def test_extract_drive_file_id_file_path_format():
    url = "https://drive.google.com/file/d/1h34UxeYnGT6-LK8OkkAmv_9ACbHa791I/view?usp=share_link"
    assert scrape.extract_drive_file_id(url) == "1h34UxeYnGT6-LK8OkkAmv_9ACbHa791I"


def test_extract_drive_file_id_non_drive_url_returns_none():
    assert scrape.extract_drive_file_id("https://drive.proton.me/urls/DSTDZTEJKM#0XYfm65uGe4H") is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "/Users/schwe/Downloads/Claude Projects/Moe Source" && .venv/bin/pytest tests/test_scrape.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scrape'`

- [ ] **Step 3: Create `scripts/scrape.py` with the module skeleton and `extract_drive_file_id`**

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_scrape.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/scrape.py tests/test_scrape.py
git commit -m "scrape: extract Google Drive file IDs from all 3 URL shapes"
```

---

## Task 4: `scrape.py` — parsing app cards

**Files:**
- Create: `tests/fixtures/sample_grid_page.html`
- Modify: `scripts/scrape.py`
- Modify: `tests/test_scrape.py`

- [ ] **Step 1: Create the fixture** — a real (trimmed) grid page containing 4 real app cards pulled from the live site: Carrot (`open?id=` Drive URL, has a changelog), Youtube Moe Multi (`uc?id=` Drive URL, has a changelog, `is-new` badge), Webssh (`uc?id=` Drive URL, no changelog, icon under `/static/icons/`), and the bare "Twitch" listing (`file/d/<id>/view` Drive URL, no changelog)

```html
<!DOCTYPE html>
<html>
<body>
<div class="apps-grid">

<article class="app-card"
    data-name="Carrot 6.5 Pro Moe with Working Widgets" data-updated="2026-03-26"
    data-modified="1774549323">

    <a class="app-card-open-link" href="/app/app_1758405429_2536?v=1774549323" aria-label="Open Carrot 6.5 Pro Moe with Working Widgets details"></a>
    <div class="app-header">
        <div class="app-icon">
            <img src="/uploads/icons/Carrot_6.3.1_Pro_Moe_1758405429.webp?v=1782581996.1782772118" alt="Carrot 6.5 Pro Moe with Working Widgets"
                loading="lazy" decoding="async" width="54" height="54" sizes="54px"
                onerror="handleIconError(this);" onload="handleIconLoad(this);">
            <i class="fas fa-mobile-alt fallback-icon" style="display: none;"></i>
        </div>
        <div class="app-info">
            <h3>Carrot 6.5 Pro Moe with Working Widgets</h3>
        </div>
    </div>

    <p class="app-description">Carrot 6.5 Pro Moe with Working Widgets for iOS, listed on Moe&#39;s App Hub with version, file size, and install details. L...</p>

    <div class="app-changelog-preview">
        <span class="changelog-text">requires the use of a custom entitlement file from your cert.</span>
    </div>

    <div class="app-meta">
        <div class="app-meta-row">
            <span>v6.5</span>
            <span>419.92 MB</span>
        </div>
        <div class="app-timestamp">3 months ago &middot; Mar 26 1:22pm CST</div>
    </div>

    <div class="app-actions">
        <a href="https://drive.google.com/open?id=1Ik0i3j-apPlTITfnMMyA0CmEfjbKOqrE&amp;usp=drive_fs" target="_blank" rel="noopener noreferrer" class="app-action primary download-link"
            onclick="event.stopPropagation()">
            <i class="fas fa-download"></i>
            Download
        </a>
        <a href="https://apps.apple.com/app/id961390574" target="_blank" rel="noopener noreferrer" class="app-action"
            onclick="event.stopPropagation()">
            App Store
        </a>
        <a href="/app/app_1758405429_2536?v=1774549323" class="app-action" onclick="event.stopPropagation()">
            <i class="fas fa-info-circle"></i>
            Details
        </a>
    </div>
</article>

<article class="app-card is-new"
    data-name="Youtube 21.26.4 Moe Multi 10.11" data-updated="2026-06-29"
    data-modified="1782770755">
    <div class="new-badge">NEW</div>
    <a class="app-card-open-link" href="/app/app_1757018667_5902?v=1782770755" aria-label="Open Youtube 21.26.4 Moe Multi 10.11 details"></a>
    <div class="app-header">
        <div class="app-icon">
            <img src="/uploads/icons/Youtube_20.37.3_Multi_2.7.5_Moe_Patched_1758409576.webp?v=1782581996.1782772118" alt="Youtube 21.26.4 Moe Multi 10.11"
                loading="lazy" decoding="async" width="54" height="54" sizes="54px"
                onerror="handleIconError(this);" onload="handleIconLoad(this);">
            <i class="fas fa-mobile-alt fallback-icon" style="display: none;"></i>
        </div>
        <div class="app-info">
            <h3>Youtube 21.26.4 Moe Multi 10.11</h3>
        </div>
    </div>

    <p class="app-description">DONT SIGN WITH ESIGN AND hold down with 4 fingers to open multi menu</p>

    <div class="app-changelog-preview">
        <span class="changelog-text">Included tweaks:
- YTKillerPlus
- DLTube
- TubeLRD
- YTLite
- YTReborn
- YouTubeX
- YTSy
- DontEatMyContent
- YouTubeDislikesReturn
- and more</span>
    </div>

    <div class="app-meta">
        <div class="app-meta-row">
            <span>v21.26.4</span>
            <span>190.3 MB</span>
        </div>
        <div class="app-timestamp">1 day ago &middot; Jun 29 5:05pm CST</div>
    </div>

    <div class="app-actions">
        <a href="https://drive.google.com/uc?id=1eigsUQ10jGGhUyV658Vw6wUO8mZC9ej_&amp;export=download" target="_blank" rel="noopener noreferrer" class="app-action primary download-link"
            onclick="event.stopPropagation()">
            <i class="fas fa-download"></i>
            Download
        </a>
        <a href="https://apps.apple.com/app/id544007664" target="_blank" rel="noopener noreferrer" class="app-action"
            onclick="event.stopPropagation()">
            App Store
        </a>
        <a href="/app/app_1757018667_5902?v=1782770755" class="app-action" onclick="event.stopPropagation()">
            <i class="fas fa-info-circle"></i>
            Details
        </a>
    </div>
</article>

<article class="app-card"
    data-name="Webssh 32.1 Pro" data-updated="2026-06-04"
    data-modified="1780605393" data-created="">

    <a class="app-card-open-link" href="/app/app_1757008016_7340?v=1780605393" aria-label="Open Webssh 32.1 Pro details"></a>
    <div class="app-header">
        <div class="app-icon">
            <img src="/static/icons/WebSSH_xlarge.webp?v=1782581996.1782772118" alt="Webssh 32.1 Pro"
                loading="lazy" decoding="async" width="54" height="54" sizes="54px"
                onerror="handleIconError(this);" onload="handleIconLoad(this);">
            <i class="fas fa-mobile-alt fallback-icon" style="display: none;"></i>
        </div>
        <div class="app-info">
            <h3>Webssh 32.1 Pro</h3>
        </div>
    </div>

    <p class="app-description is-expanded">Webssh 32.1 Pro for iOS.</p>

    <div class="app-meta">
        <div class="app-meta-row">
            <span>v32.1</span>
            <span>92.3 MB</span>
        </div>
        <div class="app-timestamp">3 weeks ago &middot; Jun 4 3:36pm CST</div>
    </div>

    <div class="app-actions">
        <a href="https://drive.google.com/uc?id=1fDpEIT7R8eXZi_KDu2_uKkUkIPmwtMjy&amp;export=download" target="_blank" rel="noopener noreferrer" class="app-action primary download-link"
            onclick="event.stopPropagation()">
            <i class="fas fa-download"></i>
            Download
        </a>
        <a href="https://apps.apple.com/app/id497714887" target="_blank" rel="noopener noreferrer" class="app-action"
            onclick="event.stopPropagation()">
            App Store
        </a>
        <a href="/app/app_1757008016_7340?v=1780605393" class="app-action" onclick="event.stopPropagation()">
            <i class="fas fa-info-circle"></i>
            Details
        </a>
    </div>
</article>

<article class="app-card"
    data-name="Twitch" data-updated="2025-08-29"
    data-modified="1758400161" data-created="">

    <a class="app-card-open-link" href="/app/app_1757008016_1558?v=1758400161" aria-label="Open Twitch details"></a>
    <div class="app-header">
        <div class="app-icon">
            <img src="/static/icons/Twitch_xlarge.webp?v=1782581996.1782772118" alt="Twitch"
                loading="lazy" decoding="async" width="54" height="54" sizes="54px"
                onerror="handleIconError(this);" onload="handleIconLoad(this);">
            <i class="fas fa-mobile-alt fallback-icon" style="display: none;"></i>
        </div>
        <div class="app-info">
            <h3>Twitch</h3>
        </div>
    </div>

    <p class="app-description is-expanded">Twitch is an iOS release entry for Twitch: Live Streaming on Moe&#39;s App Hub, with version, file size, icon, and install details.</p>

    <div class="app-meta">
        <div class="app-meta-row">
            <span>v24.2.4</span>
            <span>80 MB</span>
        </div>
        <div class="app-timestamp">9 months ago &middot; Sep 20 3:29pm CST</div>
    </div>

    <div class="app-actions">
        <a href="https://drive.google.com/file/d/1h34UxeYnGT6-LK8OkkAmv_9ACbHa791I/view?usp=share_link" target="_blank" rel="noopener noreferrer" class="app-action primary download-link"
            onclick="event.stopPropagation()">
            <i class="fas fa-download"></i>
            Download
        </a>
        <a href="https://apps.apple.com/app/id460177396" target="_blank" rel="noopener noreferrer" class="app-action"
            onclick="event.stopPropagation()">
            App Store
        </a>
        <a href="/app/app_1757008016_1558?v=1758400161" class="app-action" onclick="event.stopPropagation()">
            <i class="fas fa-info-circle"></i>
            Details
        </a>
    </div>
</article>

</div>
</body>
</html>
```

- [ ] **Step 2: Add the failing tests**

```python
# append to tests/test_scrape.py
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_grid_page.html"


def test_parse_app_cards_extracts_all_cards_from_fixture():
    html = FIXTURE_PATH.read_text()
    cards = scrape.parse_app_cards(html)
    assert len(cards) == 4
    ids = {card.app_id for card in cards}
    assert ids == {
        "app_1758405429_2536",  # Carrot
        "app_1757018667_5902",  # Youtube Moe Multi
        "app_1757008016_7340",  # Webssh
        "app_1757008016_1558",  # Twitch bare
    }


def test_parse_app_cards_reads_youtube_moe_multi_fields():
    html = FIXTURE_PATH.read_text()
    cards = {card.app_id: card for card in scrape.parse_app_cards(html)}
    youtube = cards["app_1757018667_5902"]
    assert youtube.name == "Youtube 21.26.4 Moe Multi 10.11"
    assert youtube.data_modified == 1782770755
    assert youtube.version_text == "v21.26.4"
    assert youtube.size_text == "190.3 MB"
    assert youtube.drive_file_id == "1eigsUQ10jGGhUyV658Vw6wUO8mZC9ej_"
    assert youtube.changelog is not None
    assert "YTKillerPlus" in youtube.changelog
    assert youtube.icon_url == (
        "https://moe.mohkg1017.pro/uploads/icons/"
        "Youtube_20.37.3_Multi_2.7.5_Moe_Patched_1758409576.webp"
        "?v=1782581996.1782772118"
    )


def test_parse_app_cards_handles_card_with_no_changelog():
    html = FIXTURE_PATH.read_text()
    cards = {card.app_id: card for card in scrape.parse_app_cards(html)}
    webssh = cards["app_1757008016_7340"]
    assert webssh.changelog is None
    assert webssh.version_text == "v32.1"
    assert webssh.icon_url == (
        "https://moe.mohkg1017.pro/static/icons/WebSSH_xlarge.webp"
        "?v=1782581996.1782772118"
    )


def test_parse_app_cards_handles_file_d_drive_url():
    html = FIXTURE_PATH.read_text()
    cards = {card.app_id: card for card in scrape.parse_app_cards(html)}
    twitch = cards["app_1757008016_1558"]
    assert twitch.drive_file_id == "1h34UxeYnGT6-LK8OkkAmv_9ACbHa791I"
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_scrape.py -v`
Expected: FAIL — `AttributeError: module 'scrape' has no attribute 'parse_app_cards'`

- [ ] **Step 4: Add `parse_app_cards` to `scripts/scrape.py`** (append below `extract_drive_file_id`)

```python
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
    return cards
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_scrape.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/scrape.py tests/test_scrape.py tests/fixtures/sample_grid_page.html
git commit -m "scrape: parse app cards into AppCard records"
```

---

## Task 5: `scrape.py` — fetching pages and aggregating tracked apps

**Files:**
- Modify: `scripts/scrape.py`
- Modify: `tests/test_scrape.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_scrape.py
import requests


def test_fetch_page_requests_correct_url_and_params(monkeypatch):
    captured = {}

    class FakeResponse:
        text = "<html></html>"

        def raise_for_status(self):
            pass

    def fake_get(self, url, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = dict(self.headers)
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "get", fake_get)
    session = requests.Session()
    session.headers["User-Agent"] = scrape.USER_AGENT

    html = scrape.fetch_page(session, 3)

    assert html == "<html></html>"
    assert captured["url"] == f"{scrape.BASE_URL}/"
    assert captured["params"] == {"page": 3}
    assert captured["headers"]["User-Agent"] == scrape.USER_AGENT


def test_scrape_tracked_apps_aggregates_across_pages(monkeypatch):
    fixture_html = FIXTURE_PATH.read_text()
    pages_returned = []

    def fake_fetch_page(session, page):
        pages_returned.append(page)
        if page == 1:
            return fixture_html
        return "<html><div class='apps-grid'></div></html>"

    monkeypatch.setattr(scrape, "fetch_page", fake_fetch_page)
    monkeypatch.setattr(scrape, "NUM_PAGES", 2)
    monkeypatch.setattr(scrape, "PAGE_DELAY_SECONDS", 0)

    found = scrape.scrape_tracked_apps({"app_1758405429_2536", "app_1757008016_7340"})

    assert pages_returned == [1, 2]
    assert set(found.keys()) == {"app_1758405429_2536", "app_1757008016_7340"}
    assert found["app_1758405429_2536"].name == "Carrot 6.5 Pro Moe with Working Widgets"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_scrape.py -v`
Expected: FAIL — `AttributeError: module 'scrape' has no attribute 'fetch_page'`

- [ ] **Step 3: Add `fetch_page` and `scrape_tracked_apps` to `scripts/scrape.py`** (append at the end of the file)

```python
def fetch_page(session: requests.Session, page: int) -> str:
    response = session.get(f"{BASE_URL}/", params={"page": page}, timeout=30)
    response.raise_for_status()
    return response.text


def scrape_tracked_apps(tracked_ids: set[str]) -> dict[str, AppCard]:
    """Scan all grid pages, return the latest card for every tracked app_id found."""
    session = requests.Session()
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_scrape.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/scrape.py tests/test_scrape.py
git commit -m "scrape: fetch grid pages and aggregate tracked-app cards"
```

---

## Task 6: `process_app.py` — file hashing and Info.plist extraction

**Files:**
- Create: `scripts/process_app.py`
- Test: `tests/test_process_app.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_process_app.py
import hashlib
import plistlib
import zipfile

import process_app


def test_sha256_and_size_of_known_content(tmp_path):
    file_path = tmp_path / "sample.bin"
    content = b"hello moe altstore"
    file_path.write_bytes(content)

    digest, size = process_app.sha256_and_size(file_path)

    assert digest == hashlib.sha256(content).hexdigest()
    assert size == len(content)


def test_extract_bundle_info_reads_info_plist(tmp_path):
    ipa_path = tmp_path / "sample.ipa"
    plist_bytes = plistlib.dumps(
        {
            "CFBundleIdentifier": "com.example.testapp",
            "CFBundleShortVersionString": "1.2.3",
        }
    )
    with zipfile.ZipFile(ipa_path, "w") as ipa:
        ipa.writestr("Payload/TestApp.app/Info.plist", plist_bytes)
        ipa.writestr("Payload/TestApp.app/TestApp", b"fake binary")

    bundle_id, version = process_app.extract_bundle_info(ipa_path)

    assert bundle_id == "com.example.testapp"
    assert version == "1.2.3"


def test_extract_bundle_info_raises_when_missing(tmp_path):
    ipa_path = tmp_path / "empty.ipa"
    with zipfile.ZipFile(ipa_path, "w") as ipa:
        ipa.writestr("Payload/readme.txt", b"nothing here")

    try:
        process_app.extract_bundle_info(ipa_path)
        assert False, "expected ValueError"
    except ValueError:
        pass
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_process_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'process_app'`

- [ ] **Step 3: Create `scripts/process_app.py` with `sha256_and_size` and `extract_bundle_info`**

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_process_app.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/process_app.py tests/test_process_app.py
git commit -m "process_app: sha256/size hashing and Info.plist extraction"
```

---

## Task 7: `process_app.py` — icon conversion and downloader selection

**Files:**
- Modify: `scripts/process_app.py`
- Modify: `tests/test_process_app.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_process_app.py
import io

from PIL import Image


def test_convert_icon_to_png_produces_valid_png_from_webp():
    source_image = Image.new("RGB", (8, 8), color=(255, 0, 0))
    buffer = io.BytesIO()
    source_image.save(buffer, format="WEBP")
    webp_bytes = buffer.getvalue()

    png_bytes = process_app.convert_icon_to_png(webp_bytes)

    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    result_image = Image.open(io.BytesIO(png_bytes))
    assert result_image.format == "PNG"
    assert result_image.size == (8, 8)


def test_choose_downloader_drive_url():
    assert process_app.choose_downloader("https://drive.google.com/uc?id=X") == "gdown"


def test_choose_downloader_other_url():
    url = "https://github.com/user/repo/releases/download/v1/app.ipa"
    assert process_app.choose_downloader(url) == "requests"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_process_app.py -v`
Expected: FAIL — `AttributeError: module 'process_app' has no attribute 'convert_icon_to_png'`

- [ ] **Step 3: Add `convert_icon_to_png` and `choose_downloader` to `scripts/process_app.py`** (append at the end of the file)

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_process_app.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/process_app.py tests/test_process_app.py
git commit -m "process_app: icon-to-PNG conversion and downloader selection"
```

---

## Task 8: `process_app.py` — downloading and re-hosting

**Files:**
- Modify: `scripts/process_app.py`
- Modify: `tests/test_process_app.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_process_app.py
from types import SimpleNamespace


def test_download_ipa_uses_gdown_for_drive_urls(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(process_app, "download_via_gdown", lambda file_id, dest: calls.append(("gdown", file_id, dest)))
    monkeypatch.setattr(process_app, "download_via_requests", lambda url, dest: calls.append(("requests", url, dest)))

    card = SimpleNamespace(download_url="https://drive.google.com/uc?id=ABC123", drive_file_id="ABC123")
    dest = tmp_path / "app.ipa"
    process_app.download_ipa(card, dest)

    assert calls == [("gdown", "ABC123", dest)]


def test_download_ipa_uses_requests_for_non_drive_urls(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(process_app, "download_via_gdown", lambda file_id, dest: calls.append(("gdown", file_id, dest)))
    monkeypatch.setattr(process_app, "download_via_requests", lambda url, dest: calls.append(("requests", url, dest)))

    card = SimpleNamespace(download_url="https://github.com/user/repo/app.ipa", drive_file_id="")
    dest = tmp_path / "app.ipa"
    process_app.download_ipa(card, dest)

    assert calls == [("requests", "https://github.com/user/repo/app.ipa", dest)]


def test_upload_release_asset_creates_release_when_missing(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        result = SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:3] == ["gh", "release", "view"]:
            result.returncode = 1  # release does not exist yet
        return result

    monkeypatch.setattr(process_app.subprocess, "run", fake_run)
    asset_path = tmp_path / "App.ipa"
    asset_path.write_bytes(b"fake ipa bytes")

    url = process_app.upload_release_asset(
        "MountainofPenguin/moe-altstore", "carrot-6.5.0", asset_path, "Carrot"
    )

    assert calls[0][:3] == ["gh", "release", "view"]
    assert calls[1][:3] == ["gh", "release", "create"]
    assert calls[2][:3] == ["gh", "release", "upload"]
    assert url == (
        "https://github.com/MountainofPenguin/moe-altstore/"
        "releases/download/carrot-6.5.0/App.ipa"
    )


def test_upload_release_asset_skips_create_when_release_exists(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(process_app.subprocess, "run", fake_run)
    asset_path = tmp_path / "App.ipa"
    asset_path.write_bytes(b"fake ipa bytes")

    process_app.upload_release_asset(
        "MountainofPenguin/moe-altstore", "carrot-6.5.0", asset_path, "Carrot"
    )

    commands = [c[:3] for c in calls]
    assert ["gh", "release", "create"] not in commands
    assert ["gh", "release", "view"] in commands
    assert ["gh", "release", "upload"] in commands
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_process_app.py -v`
Expected: FAIL — `AttributeError: module 'process_app' has no attribute 'download_via_gdown'`

- [ ] **Step 3: Add downloading and upload functions to `scripts/process_app.py`** (append at the end of the file)

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_process_app.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/process_app.py tests/test_process_app.py
git commit -m "process_app: download IPAs (gdown/requests) and upload to GitHub Releases"
```

---

## Task 9: `build_source.py` — rendering apps.json

**Files:**
- Create: `scripts/build_source.py`
- Test: `tests/test_build_source.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_build_source.py
from build_source import SOURCE_IDENTIFIER, SOURCE_NAME, build_source

CONFIG_APPS = [
    {
        "app_id": "app_1758405429_2536",
        "slug": "carrot",
        "name": "Carrot",
        "subtitle": "Weather app, Moe Pro patch",
    },
    {
        "app_id": "app_1757008016_7340",
        "slug": "webssh",
        "name": "Webssh",
        "subtitle": "SSH client, Pro patch",
    },
]


def test_build_source_includes_only_apps_with_state():
    state = {
        "carrot": {
            "bundle_identifier": "com.runcarrot.weather",
            "description": "Weather app.",
            "icon_url": (
                "https://raw.githubusercontent.com/MountainofPenguin/"
                "moe-altstore/main/icons/carrot.png"
            ),
            "versions": [
                {
                    "version": "6.5.0",
                    "date": "2026-03-26T19:22:00Z",
                    "description": "Working widgets build.",
                    "download_url": (
                        "https://github.com/MountainofPenguin/moe-altstore/"
                        "releases/download/carrot-6.5.0/carrot.ipa"
                    ),
                    "size": 440401920,
                }
            ],
        }
        # "webssh" has no state entry yet -> must be omitted from output
    }

    source = build_source(CONFIG_APPS, state)

    assert source["name"] == SOURCE_NAME
    assert source["identifier"] == SOURCE_IDENTIFIER
    assert len(source["apps"]) == 1

    carrot = source["apps"][0]
    assert carrot["name"] == "Carrot"
    assert carrot["bundleIdentifier"] == "com.runcarrot.weather"
    assert carrot["developerName"] == "Moe Apps"
    assert carrot["subtitle"] == "Weather app, Moe Pro patch"
    assert carrot["localizedDescription"] == "Weather app."
    assert carrot["iconURL"].endswith("/icons/carrot.png")
    assert carrot["versions"] == [
        {
            "version": "6.5.0",
            "date": "2026-03-26T19:22:00Z",
            "localizedDescription": "Working widgets build.",
            "downloadURL": (
                "https://github.com/MountainofPenguin/moe-altstore/"
                "releases/download/carrot-6.5.0/carrot.ipa"
            ),
            "size": 440401920,
        }
    ]


def test_build_source_omits_apps_with_empty_versions_list():
    state = {"carrot": {"versions": []}}
    source = build_source(CONFIG_APPS, state)
    assert source["apps"] == []


def test_build_source_omits_apps_with_no_state_at_all():
    source = build_source(CONFIG_APPS, {})
    assert source["apps"] == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_build_source.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_source'`

- [ ] **Step 3: Create `scripts/build_source.py`**

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_build_source.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/build_source.py tests/test_build_source.py
git commit -m "build_source: render apps.json from state.json"
```

---

## Task 10: `pipeline.py` — config/state I/O and diffing

**Files:**
- Create: `scripts/pipeline.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pipeline.py
from types import SimpleNamespace

import pipeline


def test_load_config_reads_apps_yaml(tmp_path, monkeypatch):
    config_path = tmp_path / "apps.yaml"
    config_path.write_text(
        "apps:\n"
        "  - app_id: app_123\n"
        "    slug: testapp\n"
        "    name: Test App\n"
        "    subtitle: A test\n"
    )
    monkeypatch.setattr(pipeline, "CONFIG_PATH", config_path)

    config = pipeline.load_config()

    assert config == [
        {"app_id": "app_123", "slug": "testapp", "name": "Test App", "subtitle": "A test"}
    ]


def test_load_state_returns_empty_dict_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "STATE_PATH", tmp_path / "state.json")
    assert pipeline.load_state() == {}


def test_save_state_then_load_state_round_trips(tmp_path, monkeypatch):
    state_path = tmp_path / "nested" / "state.json"
    monkeypatch.setattr(pipeline, "STATE_PATH", state_path)

    pipeline.save_state({"carrot": {"data_modified": 123}})
    result = pipeline.load_state()

    assert result == {"carrot": {"data_modified": 123}}


def test_apps_needing_processing_includes_new_and_changed_only():
    config_apps = [
        {"app_id": "app_1", "slug": "new-app"},
        {"app_id": "app_2", "slug": "changed-app"},
        {"app_id": "app_3", "slug": "unchanged-app"},
        {"app_id": "app_4", "slug": "not-scraped-this-run"},
    ]
    scraped = {
        "app_1": SimpleNamespace(data_modified=100),
        "app_2": SimpleNamespace(data_modified=200),
        "app_3": SimpleNamespace(data_modified=300),
    }
    state = {
        "changed-app": {"data_modified": 199},
        "unchanged-app": {"data_modified": 300},
    }

    result = pipeline.apps_needing_processing(config_apps, scraped, state)

    assert [c["slug"] for c in result] == ["new-app", "changed-app"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline'`

- [ ] **Step 3: Create `scripts/pipeline.py` with config/state I/O and diffing**

```python
"""Orchestrates a full pipeline run: scrape, diff, process, rebuild apps.json."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_pipeline.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline.py tests/test_pipeline.py
git commit -m "pipeline: config/state I/O and change detection"
```

---

## Task 11: `pipeline.py` — full orchestration and initial `apps.json`/`state.json` seeds

This task wires the previously-tested pieces together into `run()`. `process_single_app` and `run()` are IO-heavy glue (network downloads, `gh` subprocess calls, filesystem writes) — per the design's error-handling section, each app's failure must be isolated, which means this function is inherently a thin coordinator over the already-tested pure/mockable pieces from Tasks 3–10. It's intentionally left without new unit tests here; Task 14 runs the full existing suite to confirm nothing regressed, and Task 15 does a real (network) dry run before anything is pushed live.

**Files:**
- Modify: `scripts/pipeline.py`
- Create: `apps.json` (seed)
- Create: `state/state.json` (seed)

- [ ] **Step 1: Append orchestration to `scripts/pipeline.py`**

```python
# append to scripts/pipeline.py
import tempfile
from datetime import datetime, timezone

from build_source import build_source
from process_app import (
    convert_icon_to_png,
    download_ipa,
    extract_bundle_info,
    sha256_and_size,
    upload_release_asset,
)
from scrape import scrape_tracked_apps

import requests


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
```

- [ ] **Step 2: Seed `state/state.json`** so the repo has a valid (empty) cache before the first automated run

```json
{}
```

- [ ] **Step 3: Seed `apps.json`** so the repo serves a syntactically valid (empty) AltStore source immediately, even before the first automated run completes

```json
{
  "name": "Moe AltStore",
  "identifier": "com.mountainofpenguin.moealtstore",
  "apps": []
}
```

- [ ] **Step 4: Verify the module imports cleanly**

Run: `cd "/Users/schwe/Downloads/Claude Projects/Moe Source" && .venv/bin/python3 -c "import sys; sys.path.insert(0, 'scripts'); import pipeline; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline.py state/state.json apps.json
git commit -m "pipeline: full run() orchestration; seed apps.json and state.json"
```

---

## Task 12: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/update.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: Update Moe AltStore source

on:
  schedule:
    - cron: "0 13 * * *"
  workflow_dispatch: {}

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run pipeline
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/pipeline.py

      - name: Commit and push changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add apps.json state/state.json icons/
          git diff --staged --quiet || git commit -m "Update apps.json [automated]"
          git push
```

- [ ] **Step 2: Validate the YAML syntax**

Run: `cd "/Users/schwe/Downloads/Claude Projects/Moe Source" && .venv/bin/python3 -c "import yaml; yaml.safe_load(open('.github/workflows/update.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/update.yml
git commit -m "Add daily GitHub Actions workflow"
```

---

## Task 13: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the stub with full usage docs**

```markdown
# Moe AltStore

An AltStore/SideStore source that mirrors a curated set of 37 apps from
[moe.mohkg1017.pro](https://moe.mohkg1017.pro), kept in sync by a daily
GitHub Actions job. IPAs are re-hosted on this repo's GitHub Releases (the
source site's Google Drive links don't serve large files directly, which
breaks on-device installs), and `apps.json` is regenerated from real
`Info.plist` data pulled from each downloaded IPA rather than the source
site's display text.

## Using this source

Add this URL as a source in AltStore or SideStore:

```
https://raw.githubusercontent.com/MountainofPenguin/moe-altstore/main/apps.json
```

## Adding or removing a tracked app

Tracked apps live in `config/apps.yaml`, keyed by the app's stable site ID
(visible in the URL of its "Details" page on moe.mohkg1017.pro, e.g.
`/app/app_1757018667_5902` → `app_1757018667_5902`). Add or remove an entry
there — no code changes needed. The next scheduled (or manually triggered)
workflow run will pick up the change.

## Known limitations

- Apps whose download link isn't Google Drive (e.g. Proton Drive share
  links, which require in-browser decryption) can't be processed by this
  pipeline and are excluded from `config/apps.yaml`.
- The first run after adding a new app processes its full IPA in one pass;
  after that, only apps whose `data-modified` timestamp changes on the
  source site get re-downloaded.

## Local development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest tests/ -v
```

Running the pipeline for real (`.venv/bin/python3 scripts/pipeline.py`)
downloads IPAs from Google Drive and uploads GitHub Release assets to this
repo — it's meant to run in CI via `.github/workflows/update.yml`, not
casually from a laptop.

## Design

See `docs/superpowers/specs/2026-06-30-moe-altstore-design.md` for the full
design rationale (why GitHub Releases instead of linking Drive directly, why
apps are keyed by site ID instead of name, etc).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Write full README: usage, config, limitations, local dev"
```

---

## Task 14: Full local test suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite**

Run: `cd "/Users/schwe/Downloads/Claude Projects/Moe Source" && .venv/bin/pytest tests/ -v`
Expected: 27 passed, 0 failed (10 in `test_scrape.py`, 10 in `test_process_app.py`, 3 in `test_build_source.py`, 4 in `test_pipeline.py`)

- [ ] **Step 2: If anything fails, fix it before proceeding** — do not move on to Task 15 with a red test suite.

---

## Task 15: Live scrape dry run (no downloads, no writes)

Confirms the real site still matches what Tasks 3–5 assumed, before trusting the pipeline with real downloads/uploads. This talks to the live site over the network but does not download any IPAs or write any files.

**Files:** none (verification only)

- [ ] **Step 1: Run a scrape-only check against the live site**

Run:
```bash
cd "/Users/schwe/Downloads/Claude Projects/Moe Source" && PYTHONPATH=scripts .venv/bin/python3 -c "
import yaml
from scrape import scrape_tracked_apps

config = yaml.safe_load(open('config/apps.yaml'))['apps']
tracked = {c['app_id'] for c in config}
found = scrape_tracked_apps(tracked)
print(f'{len(found)}/{len(tracked)} tracked apps found')
missing = tracked - found.keys()
if missing:
    print('MISSING:', missing)
"
```

Expected: `37/37 tracked apps found`, no `MISSING` line. If some are missing, check whether that listing was removed from the source site (drop it from `config/apps.yaml`) or whether the site's markup changed (revisit `parse_app_cards` in `scripts/scrape.py`).

- [ ] **Step 2: No commit** — this step doesn't change any files.

---

## Task 16: Create the GitHub repo and push

> **⚠️ Requires explicit user confirmation before running.** Creating a public GitHub repo and pushing code are visible, hard-to-fully-reverse actions. Whoever executes this task must pause and get the user's go-ahead immediately before Step 2, even though the user already approved "public repo" as a design decision — that was approval of the plan, not a standing authorization to execute it unattended.

**Files:** none (repo/remote operations only)

- [ ] **Step 1: Confirm `gh` is authenticated**

Run: `gh auth status`
Expected: shows an authenticated account. If not authenticated, run `gh auth login` interactively before continuing.

- [ ] **Step 2: Create the public repo** (pause for user confirmation before this step, per the warning above)

Run: `cd "/Users/schwe/Downloads/Claude Projects/Moe Source" && gh repo create MountainofPenguin/moe-altstore --public --source=. --remote=origin`
Expected: repo created, `origin` remote added.

- [ ] **Step 3: Push**

Run: `git push -u origin main`
Expected: all commits from Tasks 1–13 pushed to `main`.

---

## Task 17: Trigger and monitor the first automated run

This is a handoff point, not a scripted step — the first real run downloads and re-hosts all 37 apps, which will take a while and is worth watching rather than firing and forgetting.

- [ ] **Step 1: Trigger the workflow manually**

Run: `gh workflow run update.yml --repo MountainofPenguin/moe-altstore`

- [ ] **Step 2: Watch it run**

Run: `gh run watch --repo MountainofPenguin/moe-altstore`

- [ ] **Step 3: After it completes, spot-check the result**

Run: `gh api repos/MountainofPenguin/moe-altstore/contents/apps.json --jq '.content' | base64 -d | python3 -c "import json,sys; data = json.load(sys.stdin); print(len(data['apps']), 'apps present')"`
Expected: some number of apps > 0 (won't necessarily be 37 on the very first run if any individual app hit a Google Drive rate limit — those are retried automatically on the next scheduled run per the design's error-handling section).

---

## Plan self-review notes

- **Spec coverage:** every section of the design doc maps to a task — site quirks (Drive URL shapes, icon path variants, missing changelog) → Tasks 3–4 fixtures; stable `app_id` keying → `config/apps.yaml` (Task 2) and `apps_needing_processing` (Task 10); bundle ID/version from `Info.plist` → Task 6; icon re-encoding → Task 7; GitHub Releases re-hosting → Task 8; apps.json schema mapping → Task 9; daily cron + manual trigger → Task 12; public repo requirement → Task 16.
- **Neoserver / Proton Drive:** correctly absent from `config/apps.yaml` (Task 2) per the corrected spec — not referenced anywhere in the pipeline code.
- **Type consistency checked:** `state[slug]` keys written in `process_single_app`/`run()` (Task 11) — `app_id`, `data_modified`, `bundle_identifier`, `description`, `icon_url`, `versions` (each with `version`, `date`, `description`, `download_url`, `size`, `sha256`) — match exactly what `build_source()` (Task 9) reads. `AppCard` fields produced by `parse_app_cards` (Task 4) match every attribute access in `pipeline.py` and the tests (`card.data_modified`, `card.changelog`, `card.description`, `card.icon_url`, `card.download_url`, `card.drive_file_id`, `card.app_id`).
- **No placeholders:** every step above contains complete, real code or a real command with a real expected output — no TBDs.
