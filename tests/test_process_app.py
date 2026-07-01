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
