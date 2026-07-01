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
