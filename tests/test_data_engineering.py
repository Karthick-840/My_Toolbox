import json

import pytest

from my_toolbox.core.pipeline import Checkpoint, PipelineRun, retry
from my_toolbox.core.sql_guard import is_read_only
from my_toolbox.devops import notebook_tools


def test_retry_backoff_and_giveup():
    calls, waits = [], []

    @retry(attempts=3, delay=1, backoff=2, jitter=0, sleep=waits.append)
    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("x")
        return "ok"

    assert flaky() == "ok" and waits == [1, 2]

    @retry(attempts=2, delay=0, sleep=lambda _: None)
    def bad():
        raise KeyError("k")

    with pytest.raises(KeyError):
        bad()


def test_pipeline_run_and_checkpoint(tmp_path):
    run = PipelineRun("etl")
    with run.step("load") as s:
        s["rows"] = 5
    with pytest.raises(RuntimeError), run.step("bad"):
        raise RuntimeError("boom")
    summary = run.summary()
    assert not summary["ok"] and summary["steps"][0]["rows"] == 5
    assert "boom" in summary["steps"][1]["error"]

    cp = Checkpoint(tmp_path / "cp.json")
    assert cp.run_once("a", lambda: 7) == 7
    assert cp.run_once("a", lambda: 8) is None
    assert Checkpoint(tmp_path / "cp.json").done("a")


@pytest.mark.parametrize("sql,ok", [
    ("select 1", True), ("WITH x AS (select 1) select * from x;", True),
    ("select replace(a,'x','y') from t", True),
    ("delete from t", False), ("select 1; drop table t", False),
    ("select 1 -- ok\n; drop table t", False), ("", False),
])
def test_is_read_only(sql, ok):
    assert is_read_only(sql) is ok


def test_sql_client_roundtrip(tmp_path):
    pd = pytest.importorskip("pandas")
    from my_toolbox.data.sql_tools import SQLClient

    url = f"sqlite:///{tmp_path / 'a.db'}"
    df = pd.DataFrame({"a": [1, 2, 3]})
    with SQLClient(url, read_only=False) as w:
        assert w.load(df, "t") == 3
    with SQLClient(url) as r:
        assert len(r.query("select * from t")) == 3
        with pytest.raises(PermissionError):
            r.load(df, "t")


def test_contract_and_conversion(tmp_path):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    from my_toolbox.data import quality

    df = pd.DataFrame({"id": [1, 2], "v": [10, 200]})
    contract = {"columns": {"id": {"dtype": "int64", "unique": True},
                            "v": {"max": 100}, "gone": {}}, "allow_extra_columns": False,
                "min_rows": 5}
    problems = quality.check_contract(df, contract)
    assert any("above 100" in p for p in problems) and any("missing column" in p for p in problems)
    assert any("only 2 rows" in p for p in problems)
    src = tmp_path / "d.csv"
    df.to_csv(src, index=False)
    assert quality.to_parquet(src, tmp_path / "d.parquet")["rows"] == 2


def test_notebook_strip_and_secrets(tmp_path):
    nb = {"cells": [{"cell_type": "code", "source": "AKIAABCDEFGHIJKLMNOP", "metadata": {},
                     "outputs": [{"output_type": "stream", "text": "x"}], "execution_count": 3}],
          "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    path = tmp_path / "n.ipynb"
    path.write_text(json.dumps(nb))
    found = notebook_tools.find_secrets(path)
    assert found[0]["type"] == "aws_access_key" and "AKIA" not in json.dumps(found)
    notebook_tools.strip_outputs(path)
    cell = json.loads(path.read_text())["cells"][0]
    assert cell["outputs"] == [] and cell["execution_count"] is None


def test_run_notebook_with_parameters(tmp_path):
    pytest.importorskip("nbclient")
    pytest.importorskip("ipykernel")
    import nbformat

    nb = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_code_cell("n = 1", metadata={"tags": ["parameters"]}),
        nbformat.v4.new_code_cell("print(n * 2)"),
    ])
    src = tmp_path / "in.ipynb"
    nbformat.write(nb, str(src))
    out = tmp_path / "out.ipynb"
    notebook_tools.run_notebook(src, out, parameters={"n": 21})
    executed = nbformat.read(str(out), as_version=4)
    assert executed.cells[-1].outputs[0]["text"].strip() == "42"
