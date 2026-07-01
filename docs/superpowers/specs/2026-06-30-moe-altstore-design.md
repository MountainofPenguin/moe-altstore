# Moe AltStore Source — Design

## Goal

Build a public GitHub repo (`MountainofPenguin/moe-altstore`) that serves an AltStore/SideStore-compatible source (`apps.json`), automatically kept in sync with a curated set of apps from https://moe.mohkg1017.pro (a third-party site listing modded/tweaked iOS IPAs). A daily automated job scrapes the site, detects new versions, re-hosts the IPAs reliably, and regenerates the source file.

## Site research (as of 2026-06-30)

- Server-rendered HTML, ~220 apps across 11 pages (`?page=1..11`, 21/page). No public JSON API (checked `homepage.js` — nothing beyond `/api/unread_messages` and `/polls`).
- Cloudflare blocks requests without a realistic browser `User-Agent` (plain `curl`/`WebFetch` got a 403; adding a Safari UA got 200).
- `robots.txt` allows scraping the app grid (`Disallow` only covers `/admin`, `/api/`, `/login`, `/search`, etc.).
- Each app card (`<article class="app-card" data-name="..." data-modified="...">`) links to a detail page at `/app/<app_id>?v=<ts>`, where `app_id` (e.g. `app_1757018667_5902`) is a **stable per-listing ID** — the site edits the same listing in place when a new build drops (name, version text, and download link all change; the ID does not). This ID, not the name string, is the right key to track apps by, since name text is free-form and changes with every version bump.
- Download links point to Google Drive (`drive.google.com/uc?id=...&export=download`), not a stable direct file URL. For files this size (~150–300MB), Drive serves an HTML "can't scan for viruses" interstitial instead of the raw file, which breaks both naive scraping and on-device AltStore installs.
- No bundle identifier is exposed anywhere on the site (grid or detail page). The only way to get the real `CFBundleIdentifier`/version is to download the IPA and read `Info.plist`.

## Scope: tracked apps

38 apps, selected by the user from the full ~220-listing catalog, keyed by their stable site `app_id` (recorded in `config/apps.yaml`):

| App family | Count | Notes |
|---|---|---|
| Carrot | 1 | |
| Webssh | 1 | |
| Neoserver | 1 | |
| MoeReddit | 1 | (Apollo, a separate Reddit client mod, explicitly excluded) |
| Infuse | 2 | Moe Plus, Plus 2.5 |
| Youtube | 10 | Moe Multi, Moe YTK, YTPlus (Cyan Edition), LRD, DLTube ×2, Moe LRD Cracked, Moe SY, Moe YTPlus Temp Free, Youtube Music (9.26) |
| Instagram | 17 | Moe Multi, SY, DL, LRD, AC, BH, IGFormat, INK Plus, RyukGram, NYX ×2, Regram, Rocket, SC, Theta |
| Twitch | 5 | bare "Twitch" listing (no version shown — handled as a degraded/skippable case), Adfree, Tweach, TwitchControl, Twitchv/Tweach |

Excluded per explicit decision: "YTmusic 9.14" (separate, older listing from a different modder than the included "Youtube Music 9.26").

`config/apps.yaml` is user-editable — adding/removing a tracked app later means adding/removing an `app_id` entry, not touching scraper code.

## Repo layout

```
moe-altstore/
├── apps.json                      # generated AltStore source — never hand-edited
├── config/apps.yaml                # tracked apps: site app_id -> slug/label
├── state/state.json                # per-app cache: last data-modified, bundle id,
│                                    #   real version, sha256, size, release tag/asset URL
├── icons/<slug>.png                # re-encoded icons, committed to git
├── scripts/
│   ├── scrape.py                   # fetch all 11 pages, extract cards for tracked app_ids
│   ├── process_app.py              # download IPA (gdown), read Info.plist, upload release
│   ├── build_source.py             # render apps.json from state.json
│   └── pipeline.py                 # orchestrates the above
├── .github/workflows/update.yml    # daily cron (also workflow_dispatch for manual runs)
└── README.md
```

## Pipeline (daily run)

1. **Scrape**: GET `?page=1..11` with a browser-like User-Agent, ~1-2s delay between requests. Parse every `app-card`; keep only cards whose `app_id` is in `config/apps.yaml`.
2. **Diff against state**: compare scraped `data-modified` to the cached value in `state/state.json`. Unchanged → skip (no download this run). New/changed → queue.
3. **Process each queued app**:
   - Download the IPA via `gdown` (handles Drive's confirm-token interstitial for large files).
   - `unzip -p *.ipa 'Payload/*.app/Info.plist'` → parse with `plistlib` → real `CFBundleIdentifier` + `CFBundleShortVersionString`.
   - Compute sha256 and exact byte size.
   - Re-encode the site's icon (webp) to PNG (avoids relying on WebP decode support in AltStore's icon renderer, and avoids a live dependency on the source site's `/uploads/` staying up).
4. **Re-host**: upload the IPA as a GitHub Release asset (tag `<slug>-<version>`); commit the PNG icon under `icons/`.
5. **Update state**: write the new version into `state/state.json`. Versions accumulate over time rather than being overwritten — since we permanently re-host every processed build, `apps.json` can offer real version history, which the source site itself doesn't (it only ever shows the current build).
6. **Rebuild `apps.json`** deterministically from `state/state.json` (full regenerate, not a patch).
7. **Commit & push** if `apps.json`, `state/state.json`, or any icon changed.

## apps.json field mapping (AltStore source schema)

Top level: `name: "Moe AltStore"`, `identifier: "com.mountainofpenguin.moealtstore"` (reverse-DNS, required by AltStore to distinguish sources), `apps: [...]`.

Per app:

| Field | Source |
|---|---|
| `name` | The `config/apps.yaml` label for that app_id (a stable human name, e.g. "YouTube (Moe Multi)") — not the raw site string, since that changes every version bump |
| `bundleIdentifier`, `versions[].version` | Real values from `Info.plist` (not the site's display text) |
| `versions[].downloadURL` | Our GitHub Release asset |
| `versions[].date` | Site's `data-modified` timestamp, converted to ISO 8601 |
| `versions[].localizedDescription` | Site's per-version changelog / "included tweaks" list, if present |
| `versions[].size` | Exact byte count of the downloaded file |
| `iconURL` | Our committed PNG under `icons/` |
| `localizedDescription` | Site's app description |
| `subtitle` | Short label derived from the tracked app's family (e.g. "Moe Multi tweak loader") |
| `developerName` | Fixed string `"Moe Apps"` (these are heavily modded builds, not attributable to original devs) |
| `tintColor` | Omitted (optional field, no reliable source data to derive it from) |

## Error handling

- Each app is processed in isolation (try/except per app). A Drive block, rate-limit, or malformed IPA fails only that app; it's logged to the GitHub Actions step summary and retried automatically on the next scheduled run. Its previous entry in `apps.json`/`state.json` is left untouched.
- Listings with missing/degraded data (e.g. the bare "Twitch" entry with no version) are skipped with a warning, not treated as fatal.
- If a tracked `app_id` 404s (removed from the site), the last-known-good entry is kept rather than deleted automatically — removal from the source is a manual edit to `config/apps.yaml`.

## Automation

- GitHub Actions workflow, daily cron + `workflow_dispatch` for on-demand runs.
- Public repo (required — AltStore fetches `apps.json` and release assets unauthenticated; a private repo would break the core use case).

## Accepted risks (explicitly signed off by user)

- First run processes all 38 apps in one pass (~38 IPA downloads + re-uploads); subsequent runs only touch changed apps.
- Hosting modded copies of copyrighted apps (YouTube, Instagram, Twitch, etc.) publicly on GitHub Releases carries real DMCA/takedown exposure for the repo.
- Google Drive may rate-limit or block the GitHub Actions runner IP on a given run; this degrades gracefully (that app is skipped and retried next run) but isn't fully preventable.
