import zipfile

import pandas as pd

from my_toolbox.directory_tools import DataStorage


def test_import_files_csv_txt_json(tmp_path, dummy_logger):
    ds = DataStorage(dummy_logger)

    csv_file = tmp_path / "a.csv"
    txt_file = tmp_path / "b.txt"
    json_file = tmp_path / "c.json"

    csv_file.write_text("x,y\n1,2\n", encoding="utf-8")
    txt_file.write_text("x\ty\n3\t4\n", encoding="utf-8")
    json_file.write_text('[{"x":5,"y":6}]', encoding="utf-8")

    assert list(ds.import_files(str(csv_file)).columns) == ["x", "y"]
    assert list(ds.import_files(str(txt_file)).columns) == ["x", "y"]
    assert list(ds.import_files(str(json_file)).columns) == ["x", "y"]


def test_import_files_unsupported_returns_empty(tmp_path, dummy_logger):
    ds = DataStorage(dummy_logger)
    bad_file = tmp_path / "bad.xyz"
    bad_file.write_text("abc", encoding="utf-8")
    out = ds.import_files(str(bad_file))
    assert isinstance(out, pd.DataFrame)
    assert out.empty


def test_save_files_csv_and_txt(tmp_path, dummy_logger):
    ds = DataStorage(dummy_logger)

    csv_out = tmp_path / "out.csv"
    txt_out = tmp_path / "out.txt"

    df = pd.DataFrame([{"a": 1, "b": 2}])
    ds.save_files(df, str(csv_out))
    ds.save_files("hello", str(txt_out))

    assert csv_out.exists()
    assert txt_out.read_text(encoding="utf-8") == "hello"


def test_get_file_update_time_file_and_folder(tmp_path, dummy_logger):
    ds = DataStorage(dummy_logger)

    target = tmp_path / "x.txt"
    target.write_text("ok", encoding="utf-8")
    today, days = ds.get_file_update_time(str(target))
    assert isinstance(today, str)
    assert isinstance(days, int)

    folder = tmp_path / "folder"
    folder.mkdir()
    newer = folder / "new.txt"
    newer.write_text("new", encoding="utf-8")
    today2, days2 = ds.get_file_update_time(str(folder), folder=True)
    assert isinstance(today2, str)
    assert isinstance(days2, int)


def test_extract_zip_file(tmp_path, dummy_logger, monkeypatch):
    ds = DataStorage(dummy_logger)
    zip_path = tmp_path / "archive.zip"
    payload = tmp_path / "payload.txt"
    payload.write_text("z", encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(payload, arcname="payload.txt")

    monkeypatch.chdir(tmp_path)
    ds.extract_zip_file()

    extracted_dir = tmp_path / "archive"
    assert extracted_dir.exists()
    assert (extracted_dir / "payload.txt").exists()
