# Changelog

Each `## vX.Y.Z (date)` section becomes the GitHub Release notes for that tag.

## v1.3.0 (2026-12-26)

- Add `data.quality` (profile, schema compare, quality issues, contracts, Parquet), `data.sql_tools.SQLClient`, `cloud.warehouse.BigQueryWarehouse`.
- Add `core.pipeline` (retry with backoff, `PipelineRun`, `Checkpoint`) and `core.sql_guard`.
- Add `devops.notebook_tools` (strip outputs, secret scan, headless run with parameters).
- MCP: data, SQL and notebook tools, data resources and prompts.
- **Behaviour change:** the MCP server is now read-only by default. Write tools need `--allow-write`. Responses and input sizes are capped.
- New extras `analytics` and `notebooks`; `mcp` now includes `analytics`.

## v1.2.0 (2026-11-26)

- Add `my_toolbox.mcp`: MCP server for PDF operations and notebook -> Medium (`pip install "my-toolbox[mcp]"`, command `my-toolbox-mcp`).
- Add `docs/skills/` usage guide for the library and the MCP server.
- Remove redundant `docs/PDF_Operations.md` and `docs/Jupyter_to_Medium.md`.

## v1.1.1 (2026-04-30)

- Restructure into `core`, `cloud`, `data`, `documents`, `web`, `devops` subpackages with optional extras.
- Add the local PDF Operations app, `PDF_FromImages`, `extract_pages`, `remove_blank_pages`, and Jupyter -> Medium publishing.
- Move to uv; replace PyPDF2 with `pypdf`; require Python 3.11-3.13.
