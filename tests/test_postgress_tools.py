import pandas as pd

import my_toolbox.postgress_tools as pg


class FakeCursor:
    def __init__(self):
        self.executed = []

    def execute(self, stmt):
        self.executed.append(stmt)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self):
        self.closed = False
        self.autocommit = False
        self._cursor = FakeCursor()

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_connect_and_close(monkeypatch):
    monkeypatch.setattr(pg.psycopg2, "connect", lambda **kwargs: FakeConn())
    db = pg.PostgreSQLDatabase("d", "u", "p")
    db.connect()
    assert db.connection is not None
    db.close()
    assert db.connection.closed is True


def test_create_database(monkeypatch):
    monkeypatch.setattr(pg.psycopg2, "connect", lambda **kwargs: FakeConn())
    db = pg.PostgreSQLDatabase("d", "u", "p")
    db.create_database("new_db")


def test_create_table_get_insert_delete(monkeypatch):
    conn = FakeConn()
    monkeypatch.setattr(pg.psycopg2, "connect", lambda **kwargs: conn)
    monkeypatch.setattr(pg.pd, "read_sql_query", lambda q, c: pd.DataFrame([{"x": 1}]))

    calls = {"to_sql": 0}

    def fake_engine(_url):
        return object()

    monkeypatch.setattr(pg, "create_engine", fake_engine)

    def fake_to_sql(self, *args, **kwargs):
        calls["to_sql"] += 1

    monkeypatch.setattr(pd.DataFrame, "to_sql", fake_to_sql)

    db = pg.PostgreSQLDatabase("d", "u", "p")
    db.connect()
    db.create_table("t", {"id": "INT"})

    out = db.get_data("select 1")
    assert not out.empty

    db.insert_data({"id": 1}, "t")
    assert calls["to_sql"] == 1

    db.delete_data("t", "id=1")
