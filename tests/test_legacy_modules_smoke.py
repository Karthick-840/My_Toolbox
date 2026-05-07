import importlib
import sys
import types
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_ms_tools_convert_excel_file(monkeypatch, tmp_path):
    from my_toolbox import ms_tools

    sample_df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    monkeypatch.setattr(ms_tools.pd, "read_excel", lambda _path: sample_df)

    csv_out = tmp_path / "out.csv"
    jsonl_out = tmp_path / "out.jsonl"

    ms_tools.convert_excel_file("dummy.xlsx", str(csv_out), "csv")
    ms_tools.convert_excel_file("dummy.xlsx", str(jsonl_out), "jsonl")

    assert csv_out.exists()
    assert jsonl_out.exists()


def test_calendar_tool_create_ics(tmp_path):
    fake_ical = types.ModuleType("icalendar")

    class _Cal:
        def __init__(self):
            self._items = []

        def add(self, *_args, **_kwargs):
            return None

        def add_component(self, event):
            self._items.append(event)

        def to_ical(self):
            return b"BEGIN:VCALENDAR\nEND:VCALENDAR\n"

    class _Event:
        def add(self, *_args, **_kwargs):
            return None

    fake_ical.Calendar = _Cal
    fake_ical.Event = _Event
    sys.modules["icalendar"] = fake_ical

    from my_toolbox.calender_tools import CalendarTool
    import pytz
    from datetime import datetime

    tool = CalendarTool(output_dir=str(tmp_path))
    out = tool.create_ics("Study", datetime.now(pytz.utc), filename="study.ics")
    assert Path(out).exists()


def test_email_tools_with_stubbed_src_config(monkeypatch, tmp_path):
    fake_src = types.ModuleType("src")
    fake_config = types.ModuleType("src.config")
    fake_config.EMAIL_CREDENTIALS = {"username": "u", "password": "p"}
    fake_config.EMAIL_FOLDERS = ["INBOX"]
    fake_config.DATA_ATTACHMENT_PATH = str(tmp_path)

    sys.modules["src"] = fake_src
    sys.modules["src.config"] = fake_config

    email_tools = importlib.import_module("my_toolbox.email_tools")

    class _FakeMail:
        def login(self, *_args, **_kwargs):
            return None

        def select(self, *_args, **_kwargs):
            return "OK", []

        def search(self, *_args, **_kwargs):
            return "OK", [b"1"]

        def fetch(self, *_args, **_kwargs):
            raw = (
                b"From: a@b.com\n"
                b"Subject: test\n"
                b"MIME-Version: 1.0\n"
                b"Content-Type: multipart/mixed; boundary=BOUNDARY\n\n"
                b"--BOUNDARY\n"
                b"Content-Type: text/plain\n\n"
                b"hello\n"
                b"--BOUNDARY\n"
                b"Content-Type: application/octet-stream\n"
                b"Content-Disposition: attachment; filename=test.txt\n"
                b"Content-Transfer-Encoding: base64\n\n"
                b"aGVsbG8=\n"
                b"--BOUNDARY--\n"
            )
            return "OK", [(None, raw)]

        def close(self):
            return None

        def logout(self):
            return None

    monkeypatch.setattr(email_tools.imaplib, "IMAP4_SSL", lambda *_args, **_kwargs: _FakeMail())

    files = list(email_tools.search_emails_with_attachments())
    assert len(files) == 1
    assert Path(files[0]).exists()


def test_financial_data_processor_with_stubs(monkeypatch, tmp_path):
    fake_utils = types.ModuleType("utils")
    fake_utils.get_api_key = lambda _name: "key"
    fake_utils.load_documents_from_csv = lambda *_args, **_kwargs: []

    fake_doc_mod = types.ModuleType("langchain.docstore.document")

    class _Doc:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

        def dict(self):
            return {"page_content": self.page_content, "metadata": self.metadata}

    fake_doc_mod.Document = _Doc

    sys.modules["utils"] = fake_utils
    sys.modules["langchain"] = types.ModuleType("langchain")
    sys.modules["langchain.docstore"] = types.ModuleType("langchain.docstore")
    sys.modules["langchain.docstore.document"] = fake_doc_mod

    fdp = importlib.import_module("finance_toolbox.financial_data_processor")

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"date": "2024-01-01", "value": 1, "economicIndicator": "GDP"}]

    monkeypatch.setattr(fdp.requests, "get", lambda *_args, **_kwargs: _Resp())

    processor = fdp.FinancialDataProcessor()
    econ = processor.fetch_economic_indicators()
    assert not econ.empty

    out = processor.process_and_save_economic_indicators(output_dir=str(tmp_path))
    assert Path(out).exists()


def test_legacy_finance_modules_compile_only():
    import py_compile

    targets = [
        ROOT / "finance_toolbox" / "main.py",
        ROOT / "finance_toolbox" / "financial_reporter.py",
        ROOT / "finance_toolbox" / "yfinance_tools.py",
    ]

    for target in targets:
        py_compile.compile(str(target), doraise=True)
