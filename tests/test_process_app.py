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
