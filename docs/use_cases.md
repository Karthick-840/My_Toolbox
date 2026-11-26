# Use Cases

## What the toolbox can do (v1.3.0)

| Area | Capabilities |
|---|---|
| **core** | Decorators (retry, throttle, memoize, timing, validation). Logging. Number, string and currency parsing. Dates (business days, fiscal periods, closest-date merges). Validators (email, URL, phone, ticker). A typed error hierarchy. **Pipeline helpers:** retry with backoff, step run logs, checkpoints. A read-only SQL guard. |
| **documents** | PDF text, image and table extraction. PDF merge, split, page ranges, blank-page removal. Images to PDF. Encrypted-PDF unlock. OCR-need detection. Duplicate-file detection by hash. Signature extraction and background removal. |
| **data** | **Profiling.** Dataset profile, schema diff, quality issues, JSON data contracts, Parquet conversion. **SQL.** `SQLClient` with query and load. **Files.** Directory and file I/O (atomic saves, backups, purging old files). Excel conversion. Postgres, Mongo and Kaggle helpers. Visualization. |
| **cloud** | Google Sheets, Cloud Storage, BigQuery and Datastore. A BigQuery warehouse wrapper. |
| **web** | API client with rate limiting, a circuit breaker and backoff. Notion CRUD. Calendar `.ics` files with spaced repetition. Email attachment search. Streamlit multi-page menus. Jupyter to Medium publishing. |
| **devops** | Git repo scaffolding. Notebook hygiene (strip outputs, secret scan, headless runs with parameters). |
| **App and MCP** | A local Flask PDF app. An MCP server exposing PDFs, data files, SQL and notebooks, read-only by default. |

## Project ideas

1. **Bank-statement ETL.** Take monthly PDF statements, unlock them with a password vault, and extract the tables. Validate them with a contract, load them to Postgres or BigQuery, and chart spending in Streamlit. Uses `PDF_Security`, `extract_tables`, `check_contract`, `SQLClient`, `PipelineRun` and `Checkpoint`.
2. **Data-quality gate for pipelines.** A CLI or CI step that profiles every incoming CSV or Parquet file, diffs the schema against the last run, and fails the build if a contract breaks. Report the results to Notion. Uses `quality`, `NotionMaster` and `pipeline`.
3. **Personal analytics agent.** Connect the MCP server to Copilot or Claude. Ask it to profile a file, list data issues, or query the database. Uses the MCP data tools, `query_sql` and the prompts.
4. **Kaggle to dashboard.** Download a dataset, profile it, convert it to Parquet, and publish a Streamlit page and a Medium write-up from the notebook. Uses `KaggleTools`, `profile`, `MultiApp` and `MediumPublisher`.
5. **Notebook-to-blog pipeline.** For each notebook, scan for secrets, strip outputs, run it with parameters, and publish a draft. Uses `notebook_tools` and `MediumPublisher`.
6. **Document intake.** Watch a folder, de-duplicate by hash, flag scanned PDFs for OCR, and split, merge and rename the rest. Log each run. Uses `move_duplicates_by_hash`, `needs_ocr`, `PDF_Manipulate` and `PipelineRun`.
7. **Study planner.** Turn course notes into Notion pages and spaced-repetition calendar events (`.ics`, Google, Outlook). Uses `NotionMaster` and `CalendarTool`.
8. **Invoice and receipt collector.** Search email attachments, extract text with a regex, normalise currency, and write to Sheets or BigQuery. Uses `email_tools`, `extract_text`, `parse_currency` and `GoogleSheets`.
9. **Multi-API ingestion service.** Pull rate-limited APIs through the circuit breaker, validate with contracts, and land the data in BigQuery with checkpoints so reruns skip finished steps. Uses `ApiTools`, `CircuitBreaker`, `Checkpoint` and `BigQueryWarehouse`.
10. **Repo bootstrap CLI.** Create a repo from a list, scaffold uv and CI, and generate a `requirements.txt`. Uses `GitTools` and `project_ops`.

For data engineering and data science work, start with idea 1 or 2, since they exercise most of the newer tools. Idea 3 is the quickest way to try the MCP server.
