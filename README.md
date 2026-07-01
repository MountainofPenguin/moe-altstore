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
