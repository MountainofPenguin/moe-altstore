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
