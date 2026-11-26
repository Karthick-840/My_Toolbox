"""Uniform query/load interface over SQLAlchemy databases (extra: analytics).

Credentials come from a URL argument or the DATABASE_URL environment variable, never code.
"""

import os
from typing import Any, Dict, Optional

try:
    import pandas as pd
    from sqlalchemy import create_engine, text
except ImportError as exc:  # pragma: no cover
    raise ImportError('Install analytics extras: pip install "my-toolbox[analytics]"') from exc

from my_toolbox.core.sql_guard import is_read_only


class SQLClient:
    """query(sql) -> DataFrame, load(df, table); same shape as other warehouse helpers."""

    def __init__(self, url: Optional[str] = None, read_only: bool = True):
        url = url or os.environ.get("DATABASE_URL")
        if not url:
            raise ValueError("Pass a SQLAlchemy URL or set DATABASE_URL.")
        self.engine = create_engine(url)
        self.read_only = read_only

    def query(self, sql: str, params: Optional[Dict[str, Any]] = None,
              max_rows: Optional[int] = None) -> "pd.DataFrame":
        if self.read_only and not is_read_only(sql):
            raise PermissionError("Client is read-only; only a single SELECT/WITH statement is allowed.")
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            rows = result.fetchmany(max_rows) if max_rows else result.fetchall()
            return pd.DataFrame(rows, columns=list(result.keys()))

    def load(self, df: "pd.DataFrame", table: str, if_exists: str = "append",
             schema: Optional[str] = None) -> int:
        if self.read_only:
            raise PermissionError("Client is read-only; create it with read_only=False to load data.")
        df.to_sql(table, self.engine, schema=schema, if_exists=if_exists, index=False)
        return len(df)

    def close(self) -> None:
        self.engine.dispose()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
