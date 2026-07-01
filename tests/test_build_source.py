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
)

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
                    "date": "2026-03-26",
                    "description": "Working widgets build.",
                    "download_url": (
                        "https://github.com/MountainofPenguin/moe-altstore/"
                        "releases/download/carrot-6.5.0/carrot.ipa"
                    ),
                    "size": 440401920,
                    "min_os_version": "15.0",
                }
            ],
        }
        # "webssh" has no state entry yet -> must be omitted from output
    }

    source = build_source(CONFIG_APPS, state)

    assert source["name"] == SOURCE_NAME
    assert source["identifier"] == SOURCE_IDENTIFIER
    assert source["apiVersion"] == SOURCE_API_VERSION
    assert source["subtitle"] == SOURCE_SUBTITLE
    assert source["description"] == SOURCE_DESCRIPTION
    assert source["iconURL"] == SOURCE_ICON_URL
    assert source["website"] == SOURCE_WEBSITE
    assert source["news"] == []
    assert len(source["apps"]) == 1

    carrot = source["apps"][0]
    assert carrot["name"] == "Carrot"
    assert carrot["bundleIdentifier"] == "com.runcarrot.weather"
    assert carrot["developerName"] == "Moe Apps"
    assert carrot["subtitle"] == "Weather app, Moe Pro patch"
    assert carrot["localizedDescription"] == "Weather app."
    assert carrot["iconURL"].endswith("/icons/carrot.png")
    assert carrot["screenshots"] == []
    assert carrot["appPermissions"] == {"entitlements": [], "privacy": {}}
    assert carrot["versions"] == [
        {
            "version": "6.5.0",
            "date": "2026-03-26",
            "localizedDescription": "Working widgets build.",
            "downloadURL": (
                "https://github.com/MountainofPenguin/moe-altstore/"
                "releases/download/carrot-6.5.0/carrot.ipa"
            ),
            "size": 440401920,
            "minOSVersion": "15.0",
        }
    ]


def test_build_source_omits_apps_with_empty_versions_list():
    state = {"carrot": {"versions": []}}
    source = build_source(CONFIG_APPS, state)
    assert source["apps"] == []


def test_build_source_omits_apps_with_no_state_at_all():
    source = build_source(CONFIG_APPS, {})
    assert source["apps"] == []
