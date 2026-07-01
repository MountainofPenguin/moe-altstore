# tests/test_scrape.py
import scrape
from pathlib import Path


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


def test_parse_app_cards_skips_malformed_card_missing_data_modified():
    html = """
    <div class="apps-grid">
    <article class="app-card" data-name="Broken App">
        <a class="app-card-open-link" href="/app/app_1111111111_9999?v=1111111111"></a>
        <div class="app-header">
            <div class="app-icon">
                <img src="/static/icons/Broken_xlarge.webp" alt="Broken App">
            </div>
        </div>
        <p class="app-description">Broken App for iOS.</p>
        <div class="app-meta">
            <div class="app-meta-row">
                <span>v1.0</span>
                <span>10 MB</span>
            </div>
        </div>
        <div class="app-actions">
            <a href="https://drive.google.com/uc?id=1BrokenAppDriveId&amp;export=download" class="app-action primary download-link">Download</a>
        </div>
    </article>
    <article class="app-card" data-name="Good App" data-modified="1780000000">
        <a class="app-card-open-link" href="/app/app_2222222222_8888?v=1780000000"></a>
        <div class="app-header">
            <div class="app-icon">
                <img src="/static/icons/Good_xlarge.webp" alt="Good App">
            </div>
        </div>
        <p class="app-description">Good App for iOS.</p>
        <div class="app-meta">
            <div class="app-meta-row">
                <span>v2.0</span>
                <span>20 MB</span>
            </div>
        </div>
        <div class="app-actions">
            <a href="https://drive.google.com/uc?id=1GoodAppDriveId&amp;export=download" class="app-action primary download-link">Download</a>
        </div>
    </article>
    </div>
    """
    cards = scrape.parse_app_cards(html)
    ids = {card.app_id for card in cards}
    assert ids == {"app_2222222222_8888"}
