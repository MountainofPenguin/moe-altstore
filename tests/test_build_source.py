# tests/test_build_source.py
from build_source import (
    SOURCE_API_VERSION,
    SOURCE_DESCRIPTION,
    SOURCE_ICON_URL,
    SOURCE_IDENTIFIER,
    SOURCE_NAME,
    SOURCE_SUBTITLE,
    SOURCE_WEBSITE,
    build_source,
    compose_version,
)

CONFIG_APPS = [
    {
        "app_id": "app_1758405429_2536",
        "slug": "carrot",
        "name": "Carrot",
        "subtitle": "Weather app, Moe Pro patch",
    },
    {
        "app_id": "app_1757018667_5902",
        "slug": "youtube-moe-multi",
        "name": "YouTube (Moe Multi)",
        "subtitle": "Multi-tweak loader",
    },
]


def test_compose_version_extracts_trailing_tweak_version():
    assert (
        compose_version("21.28.3", "Youtube 21.28.3 Moe Multi 10.16 Not Stable")
        == "21.28.3 (10.16)"
    )


def test_compose_version_handles_tweak_before_trailing_words():
    assert (
        compose_version("2026.28.1", "Reddit 2026.28.1 Moes Reddit 2.2 With LiquidGlass")
        == "2026.28.1 (2.2)"
    )


def test_compose_version_returns_base_when_no_distinct_tweak():
    # "Webssh 32.1 Pro" has only the base version token.
    assert compose_version("32.1", "Webssh 32.1 Pro") == "32.1"


def test_compose_version_returns_base_when_name_empty():
    assert compose_version("6.5", "") == "6.5"
    assert compose_version("6.5", None) == "6.5"


def test_compose_version_ignores_trailing_zero_base_reformat():
    # plist base "436.0.0" written as "436.0" in the site name is the SAME
    # version, not a tweak version — must not become "436.0.0 (436.0)".
    assert compose_version("436.0.0", "Instagram 436.0 SY tweak") == "436.0.0"


def test_compose_version_ignores_leading_zero_base_reformat():
    assert (
        compose_version("21.08.3", "Youtube 21.8.3 Moe Multi 10.16")
        == "21.08.3 (10.16)"
    )


def test_build_source_composes_version_and_omits_internal_fields():
    state = {
        "youtube-moe-multi": {
            "bundle_identifier": "com.google.ios.youtube",
            "description": "Multi-tweak YouTube.",
            "icon_url": (
                "https://raw.githubusercontent.com/MountainofPenguin/"
                "moe-altstore/main/icons/youtube-moe-multi.png"
            ),
            "versions": [
                {
                    "version": "21.28.3",
                    "display_name": "Youtube 21.28.3 Moe Multi 10.16 Not Stable",
                    "data_modified": 1784320088,
                    "date": "2026-07-17",
                    "description": "Included tweaks: ...",
                    "download_url": (
                        "https://github.com/MountainofPenguin/moe-altstore/"
                        "releases/download/youtube-moe-multi-21.28.3/youtube-moe-multi.ipa"
                    ),
                    "size": 199000000,
                    "sha256": "abc123",
                    "min_os_version": "15.0",
                }
            ],
        }
    }

    source = build_source(CONFIG_APPS, state)

    assert len(source["apps"]) == 1
    app = source["apps"][0]
    assert app["name"] == "YouTube (Moe Multi)"
    version = app["versions"][0]
    assert version["version"] == "21.28.3 (10.16)"
    assert version["date"] == "2026-07-17"
    assert version["localizedDescription"] == "Included tweaks: ..."
    assert version["downloadURL"].endswith("youtube-moe-multi.ipa")
    assert version["size"] == 199000000
    assert version["minOSVersion"] == "15.0"
    # Internal-only fields must not leak into the emitted source.
    assert "display_name" not in version
    assert "data_modified" not in version
    assert "sha256" not in version


def test_build_source_orders_versions_newest_first():
    state = {
        "youtube-moe-multi": {
            "bundle_identifier": "com.google.ios.youtube",
            "description": "Multi-tweak YouTube.",
            "icon_url": "https://example.invalid/icon.png",
            "versions": [
                {
                    "version": "21.24.3",
                    "display_name": "Youtube 21.24.3 Moe Multi 10.10",
                    "data_modified": 1000,
                    "date": "2026-07-10",
                    "description": "old",
                    "download_url": "https://example.invalid/old.ipa",
                    "size": 1,
                    "sha256": "x",
                    "min_os_version": "15.0",
                },
                {
                    "version": "21.28.3",
                    "display_name": "Youtube 21.28.3 Moe Multi 10.16",
                    "data_modified": 3000,
                    "date": "2026-07-17",
                    "description": "new",
                    "download_url": "https://example.invalid/new.ipa",
                    "size": 2,
                    "sha256": "y",
                    "min_os_version": "15.0",
                },
                {
                    "version": "21.26.4",
                    "display_name": "Youtube 21.26.4 Moe Multi 10.13",
                    "data_modified": 2000,
                    "date": "2026-07-14",
                    "description": "middle",
                    "download_url": "https://example.invalid/mid.ipa",
                    "size": 3,
                    "sha256": "z",
                    "min_os_version": "15.0",
                },
            ],
        }
    }

    source = build_source(CONFIG_APPS, state)
    versions = source["apps"][0]["versions"]
    # Newest data_modified (3000) first, then 2000, then 1000.
    assert [v["date"] for v in versions] == ["2026-07-17", "2026-07-14", "2026-07-10"]
    assert versions[0]["version"] == "21.28.3 (10.16)"


def test_build_source_top_level_shape_unchanged():
    source = build_source(CONFIG_APPS, {})
    assert source["name"] == SOURCE_NAME
    assert source["identifier"] == SOURCE_IDENTIFIER
    assert source["apiVersion"] == SOURCE_API_VERSION
    assert source["subtitle"] == SOURCE_SUBTITLE
    assert source["description"] == SOURCE_DESCRIPTION
    assert source["iconURL"] == SOURCE_ICON_URL
    assert source["website"] == SOURCE_WEBSITE
    assert source["news"] == []
    assert source["apps"] == []


def test_build_source_omits_apps_with_empty_versions_list():
    state = {"carrot": {"versions": []}}
    source = build_source(CONFIG_APPS, state)
    assert source["apps"] == []


def test_build_source_omits_apps_with_no_state_at_all():
    source = build_source(CONFIG_APPS, {})
    assert source["apps"] == []
