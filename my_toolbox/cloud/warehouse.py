"""BigQuery with the same query/load shape as my_toolbox.data.sql_tools.SQLClient (extra: cloud)."""

from typing import Optional

from my_toolbox.core.sql_guard import is_read_only


class BigQueryWarehouse:
    def __init__(self, project_id: Optional[str] = None, credentials_json: Optional[str] = None,
                 read_only: bool = True):
        from my_toolbox.cloud.gcp_tools import GoogleBigQueryHelper

        self.client = GoogleBigQueryHelper(project_id, credentials_json).client
        self.read_only = read_only

    def query(self, sql: str, max_rows: Optional[int] = None):
        if self.read_only and not is_read_only(sql):
            raise PermissionError("Warehouse is read-only; only a single SELECT/WITH is allowed.")
        return self.client.query(sql).result(max_results=max_rows).to_dataframe()

    def load(self, df, table: str, if_exists: str = "append") -> int:
        """table is 'dataset.table' (or 'project.dataset.table'); if_exists: append|replace|fail."""
        if self.read_only:
            raise PermissionError("Warehouse is read-only; create it with read_only=False to load.")
        from google.cloud import bigquery

        disposition = {"append": "WRITE_APPEND", "replace": "WRITE_TRUNCATE", "fail": "WRITE_EMPTY"}[if_exists]
        job = self.client.load_table_from_dataframe(
            df, table, job_config=bigquery.LoadJobConfig(write_disposition=disposition))
        job.result()
        return len(df)
