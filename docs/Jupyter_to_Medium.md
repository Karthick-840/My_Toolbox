# Jupyter to Medium

`my_toolbox.web.medium_tools` converts a Jupyter notebook into a Medium post and publishes it
through the Medium API. Posts are created as **drafts** by default so you can review them on Medium first.

## Setup

1. Create an integration token on Medium: *Settings > Security and apps > Integration tokens*.
2. Export it: `export MEDIUM_TOKEN=...` (or pass `token=` to `MediumPublisher`).

## Usage

```python
from my_toolbox.web.medium_tools import MediumPublisher

post = MediumPublisher().publish_notebook(
    "analysis.ipynb",
    title=None,              # defaults to the first "# Heading", then the file name
    tags=["python", "data"], # Medium keeps at most 5
    status="draft",          # "draft" | "unlisted" | "public"
)
print(post["url"])
```

Convert without publishing:

```python
from my_toolbox.web.medium_tools import load_notebook, notebook_to_markdown

markdown = notebook_to_markdown(load_notebook("analysis.ipynb"), include_code=True)
```

## What gets converted

- Markdown cells are kept as-is; code cells become fenced code blocks.
- Text output (stdout, `text/plain`) becomes a code block; errors are reduced to `ErrorName: message`.
- Image outputs (PNG, JPEG, GIF - plots, rendered figures) are uploaded to Medium and embedded.
- Cell tags: `remove-cell` drops a cell, `remove-input` hides its code, `remove-output` hides its outputs.
- The notebook's first H1 is used as the title and not repeated in the body.

## Limitations

- Styled pandas DataFrames that only exist as HTML output are not rendered; their `text/plain` form is used.
- The Medium API is no longer actively developed and can stop issuing new integration tokens.
- No Jupyter menu entry ("Deploy as Medium Post"); call the function from code or a notebook cell.
