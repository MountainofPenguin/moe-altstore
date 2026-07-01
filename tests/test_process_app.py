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
