
import my_toolbox.gcp_tools as gcp_tools


def test_require_google_sheet_deps_raises(monkeypatch):
    monkeypatch.setattr(gcp_tools, "gspread", None)
    monkeypatch.setattr(gcp_tools, "Credentials", None)
    monkeypatch.setattr(gcp_tools, "set_with_dataframe", None)
    try:
        gcp_tools._require_google_sheets_deps()
        assert False, "Expected ImportError"
    except ImportError:
        pass


def test_require_google_storage_deps_raises(monkeypatch):
    monkeypatch.setattr(gcp_tools, "storage", None)
    try:
        gcp_tools._require_google_cloud_storage_deps()
        assert False, "Expected ImportError"
    except ImportError:
        pass


def test_google_cloud_storage_basic(monkeypatch, tmp_path):
    class FakeBucket:
        def __init__(self, name):
            self.name = name
            self._properties = {
                "selfLink": "self",
                "id": "id",
                "location": "US",
                "timeCreated": "now",
                "storageClass": "STANDARD",
                "updated": "now",
            }
            self.storage_class = None
            self.location = None

        def blob(self, blob_name):
            class Blob:
                def upload_from_filename(self, _fp):
                    return None

            return Blob()

    class FakeClient:
        def __init__(self, project=None):
            self.project = project

        def list_buckets(self, max_results=100):
            return [FakeBucket("b1"), FakeBucket("b2")]

        def get_bucket(self, bucket_name):
            return FakeBucket(bucket_name)

        def bucket(self, bucket_name):
            return FakeBucket(bucket_name)

        def create_bucket(self, bucket):
            return bucket

        def download_blob_to_file(self, blob, fobj):
            fobj.write(b"data")

    class FakeStorage:
        Client = FakeClient

    monkeypatch.setattr(gcp_tools, "storage", FakeStorage)

    gcs = gcp_tools.GoogleCloudStorage(credentials_path="/tmp/fake.json", project="p")
    names = gcs.list_buckets()
    assert names == ["b1", "b2"]

    bucket, details = gcs.get_bucket("b1")
    assert bucket.name == "b1"
    assert details["location"] == "US"

    created = gcs.create_bucket("new-b")
    assert created.name == "new-b"

    target = tmp_path / "dl.txt"
    gcs.download_file_from_bucket("blob", str(target), "b1")
    assert target.exists()


def test_google_sheets_auth_missing_token(monkeypatch, dummy_logger):
    monkeypatch.setattr(gcp_tools, "gspread", object())

    class Creds:
        @staticmethod
        def from_service_account_file(_path, scopes=None):
            return object()

    class Client:
        def open_by_key(self, _sheet_id):
            class Sheet:
                def worksheets(self):
                    return []

            return Sheet()

    monkeypatch.setattr(gcp_tools, "Credentials", Creds)
    monkeypatch.setattr(gcp_tools, "set_with_dataframe", lambda *_args, **_kwargs: None)

    class GS:
        @staticmethod
        def authorize(_creds):
            return Client()

    monkeypatch.setattr(gcp_tools, "gspread", GS)
    monkeypatch.setattr(gcp_tools.os.path, "exists", lambda _p: False)

    gs = gcp_tools.GoogleSheets("sheet_id", logger=dummy_logger)
    assert gs.sheet is None
