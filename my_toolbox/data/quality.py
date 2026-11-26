"""Dataset profiling, schema comparison, quality checks and Parquet conversion (extra: analytics)."""

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    raise ImportError('Install analytics extras: pip install "my-toolbox[analytics]"') from exc

SUPPORTED = (".csv", ".tsv", ".parquet", ".json", ".jsonl", ".xlsx", ".xls")


def read_table(path, nrows: Optional[int] = None) -> "pd.DataFrame":
    """Read a CSV/TSV/Parquet/JSON/JSONL/Excel file; `nrows` caps rows where the format allows."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".csv":
        return pd.read_csv(path, nrows=nrows)
    if ext == ".tsv":
        return pd.read_csv(path, sep="\t", nrows=nrows)
    if ext == ".parquet":
        df = pd.read_parquet(path)
        return df.head(nrows) if nrows else df
    if ext in (".json", ".jsonl"):
        df = pd.read_json(path, lines=ext == ".jsonl")
        return df.head(nrows) if nrows else df
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, nrows=nrows)
    raise ValueError(f"Unsupported file type {ext!r}; use one of {SUPPORTED}")


def schema(df: "pd.DataFrame") -> Dict[str, str]:
    return {str(c): str(t) for c, t in df.dtypes.items()}


def _jsonable(value: Any) -> Any:
    if pd.isna(value) if not isinstance(value, (list, dict)) else False:
        return None
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (int, float, str, bool, type(None), list, dict)):
        return value
    return str(value)


def profile(df: "pd.DataFrame", sample_rows: int = 5) -> Dict[str, Any]:
    """Row/column counts, per-column dtype, nulls, distinct count, numeric stats and a sample."""
    columns = {}
    for col in df.columns:
        s = df[col]
        info: Dict[str, Any] = {
            "dtype": str(s.dtype),
            "nulls": int(s.isna().sum()),
            "null_pct": round(float(s.isna().mean() * 100), 2) if len(s) else 0.0,
            "distinct": int(s.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s) and s.notna().any():
            info.update(min=_jsonable(s.min()), max=_jsonable(s.max()),
                        mean=round(float(s.mean()), 4))
        columns[str(col)] = info
    sample = [{str(k): _jsonable(v) for k, v in row.items()}
              for row in df.head(sample_rows).to_dict("records")]
    return {
        "rows": int(len(df)),
        "columns": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "column_profile": columns,
        "sample": sample,
    }


def compare_schemas(a: "pd.DataFrame", b: "pd.DataFrame") -> Dict[str, Any]:
    sa, sb = schema(a), schema(b)
    return {
        "only_in_a": sorted(set(sa) - set(sb)),
        "only_in_b": sorted(set(sb) - set(sa)),
        "type_changes": {c: {"a": sa[c], "b": sb[c]} for c in sa if c in sb and sa[c] != sb[c]},
        "same": sa == sb,
    }


def quality_issues(df: "pd.DataFrame", null_threshold: float = 50.0) -> List[Dict[str, Any]]:
    """Heuristic data-quality findings: nulls, constants, duplicates, mixed types, padded text."""
    issues: List[Dict[str, Any]] = []
    dups = int(df.duplicated().sum())
    if dups:
        issues.append({"type": "duplicate_rows", "count": dups})
    for col in df.columns:
        s = df[col]
        pct = float(s.isna().mean() * 100) if len(s) else 0.0
        if len(s) and pct == 100.0:
            issues.append({"type": "all_null", "column": str(col)})
            continue
        if pct >= null_threshold:
            issues.append({"type": "high_null_pct", "column": str(col), "pct": round(pct, 2)})
        if s.nunique(dropna=True) == 1 and len(s) > 1:
            issues.append({"type": "constant_column", "column": str(col)})
        if s.dtype == object:
            kinds = {type(v).__name__ for v in s.dropna()}
            if len(kinds) > 1:
                issues.append({"type": "mixed_types", "column": str(col), "types": sorted(kinds)})
            strings = s.dropna()[s.dropna().map(lambda v: isinstance(v, str))]
            padded = int((strings != strings.str.strip()).sum())
            if padded:
                issues.append({"type": "whitespace_padding", "column": str(col), "count": padded})
    return issues


def check_contract(df: "pd.DataFrame", contract: Dict[str, Any]) -> List[str]:
    """Validate a DataFrame against a contract; returns a list of violations (empty = pass).

    contract = {
        "columns": {"id": {"dtype": "int64", "nullable": False, "unique": True,
                           "min": 0, "max": 100, "allowed": ["a", "b"]}},
        "min_rows": 1,
        "allow_extra_columns": True,
    }
    """
    problems: List[str] = []
    cols = contract.get("columns", {})
    for name, rules in cols.items():
        if name not in df.columns:
            problems.append(f"missing column: {name}")
            continue
        s = df[name]
        if "dtype" in rules and str(s.dtype) != rules["dtype"]:
            problems.append(f"{name}: dtype {s.dtype} != {rules['dtype']}")
        if rules.get("nullable") is False and s.isna().any():
            problems.append(f"{name}: contains nulls")
        if rules.get("unique") and s.duplicated().any():
            problems.append(f"{name}: not unique")
        if "min" in rules and (s.dropna() < rules["min"]).any():
            problems.append(f"{name}: values below {rules['min']}")
        if "max" in rules and (s.dropna() > rules["max"]).any():
            problems.append(f"{name}: values above {rules['max']}")
        if "allowed" in rules and (~s.dropna().isin(rules["allowed"])).any():
            problems.append(f"{name}: values outside allowed set")
    if not contract.get("allow_extra_columns", True):
        extra = [str(c) for c in df.columns if c not in cols]
        if extra:
            problems.append(f"unexpected columns: {extra}")
    if len(df) < contract.get("min_rows", 0):
        problems.append(f"only {len(df)} rows, need {contract['min_rows']}")
    return problems


def to_parquet(src, dst, compression: str = "snappy") -> Dict[str, Any]:
    """Convert a tabular file to Parquet with pandas type inference."""
    df = read_table(src).convert_dtypes()
    df.to_parquet(dst, index=False, compression=compression)
    return {"rows": int(len(df)), "columns": len(df.columns), "output": str(dst)}
