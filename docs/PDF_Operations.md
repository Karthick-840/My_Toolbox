# PDF Operations

`my_toolbox.documents.pdf_tools` provides:

1. **PDFAccess** - list and read PDFs, write text to a PDF.
2. **PDF_Extract** - extract text (whole or page-wise, optional regex), images and tables.
3. **PDF_Manipulate** - merge, split into pages, `extract_pages` (ranges like `3-7,10,12-`), `remove_blank_pages`, combine by `0001_` prefix order, sort & rename, move or delete empty PDFs.
4. **PDF_FromImages** - build a PDF from images (paths, bytes, `BytesIO`, PIL) or a folder of images.

All results are written to `output_path`; methods return the produced paths or results.

## Local app

The same operations are available in a browser UI (`app/templates/pdf_operations.html`), including
a Snap to PDF tab for pasting screenshots:

```bash
make app
```

See the README for workspace folders and requirements.

## Roadmap (not implemented yet)

- Interactive PDF editing
- Natural-language interaction with PDFs via an LLM
- Automatic categorising and tagging of PDFs
