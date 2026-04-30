import json
import os
import types

from my_toolbox.kaggle_tools import KaggleTools


def test_setup_kaggle_credentials_from_json(tmp_path, dummy_logger):
    creds = {"username": "u", "key": "k"}
    (tmp_path / "kaggle.json").write_text(json.dumps(creds), encoding="utf-8")

    k = KaggleTools(dummy_logger, kaggle_dir=str(tmp_path), move_to_read_only=False)
    k.setup_kaggle_credentials()

    assert os.environ.get("KAGGLE_USERNAME") == "u"
    assert os.environ.get("KAGGLE_KEY") == "k"


def test_kaggle_auth_prefers_env(monkeypatch, dummy_logger):
    monkeypatch.setenv("KAGGLE_USERNAME", "u")
    monkeypatch.setenv("KAGGLE_KEY", "k")
    k = KaggleTools(dummy_logger)
    called = {"setup": 0}
    monkeypatch.setattr(k, "setup_kaggle_credentials", lambda: called.update(setup=1))
    k.kaggle_auth()
    assert called["setup"] == 0


def test_download_dataset_with_mocked_kaggle(monkeypatch, tmp_path, dummy_logger):
    class FakeApi:
        authed = False
        downloaded = False

        def authenticate(self):
            self.authed = True

        def dataset_download_files(self, _name, path=None, unzip=False):
            self.downloaded = True
            assert unzip is True
            assert path

    fake_module = types.SimpleNamespace(KaggleApi=FakeApi)
    import sys

    sys.modules["kaggle"] = types.SimpleNamespace()
    sys.modules["kaggle.api"] = types.SimpleNamespace()
    sys.modules["kaggle.api.kaggle_api_extended"] = fake_module

    monkeypatch.chdir(tmp_path)
    k = KaggleTools(dummy_logger)
    k.download_dataset("owner/dataset")
