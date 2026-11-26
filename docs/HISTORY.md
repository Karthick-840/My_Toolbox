# Changelog

Each `## vX.Y.Z (date)` section becomes the GitHub Release notes for that tag.

## v1.2.0 (2026-11-26)

- Add `my_toolbox.mcp`: MCP server for PDF operations and notebook -> Medium (`pip install "my-toolbox[mcp]"`, command `my-toolbox-mcp`).
- Add `docs/skills/` usage guide for the library and the MCP server.
- Remove redundant `docs/PDF_Operations.md` and `docs/Jupyter_to_Medium.md`.

## v1.1.1 (2026-04-30)

- Restructure into `core`, `cloud`, `data`, `documents`, `web`, `devops` subpackages with optional extras.
- Add the local PDF Operations app, `PDF_FromImages`, `extract_pages`, `remove_blank_pages`, and Jupyter -> Medium publishing.
- Move to uv; replace PyPDF2 with `pypdf`; require Python 3.11-3.13.
