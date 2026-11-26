---
name: use-my-toolbox-mcp
description: Install, configure and call the my-toolbox MCP server (PDF operations and notebook-to-Medium) from an MCP client or an Ansible-provisioned host.
---

# Use the my-toolbox MCP server

## Install
```bash
pip install "my-toolbox[mcp] @ git+https://github.com/Karthick-840/My_Toolbox@v1.2.0"
```
Pin a tag. Python 3.11-3.13. `extract_tables` needs Java (tabula); `images_to_pdf` needs the `images` extra.

## Run
```bash
my-toolbox-mcp --workspace /data/work     # stdio (default)
```
Workspace = `MY_TOOLBOX_WORKSPACE` env or `--workspace` (default `./workspace`):
- `inputs/` - put source files here
- `outputs/` - results are written here

All tool arguments are **bare file names** from `inputs/`. Paths, `..` and subfolders are rejected.

## Client config (Claude Desktop / VS Code / Copilot CLI style)
```json
{
  "mcpServers": {
    "my-toolbox": {
      "command": "my-toolbox-mcp",
      "args": ["--workspace", "/data/work"],
      "env": {"MEDIUM_TOKEN": "<only for notebook_to_medium>"}
    }
  }
}
```

## Tools
| Tool | Purpose |
|---|---|
| `list_files` | List `inputs/` and `outputs/` |
| `extract_text(file, page?, pattern?)` | Text, one page, or regex matches |
| `extract_pages(file, ranges, output_name?)` | Ranges like `3-7,10,12-` |
| `merge_pdfs(files, output_name)` | Merge in the given order |
| `split_pdf(file)` | One PDF per page |
| `remove_blank_pages(file, text_only?)` | Drop blank pages |
| `images_to_pdf(images, output_name)` | Images to one PDF |
| `write_text_pdf(output_name, content)` | Plain text to PDF |
| `notebook_to_medium(notebook, title?, tags?, status?)` | Draft post; needs `MEDIUM_TOKEN` |

## Typical flow
1. Copy files into `inputs/`.
2. `list_files`, then call the operation.
3. Read results from `outputs/<name>`.

## Ansible
```yaml
- name: Install my-toolbox MCP
  ansible.builtin.pip:
    name: "my-toolbox[mcp] @ git+https://github.com/Karthick-840/My_Toolbox@v1.2.0"
    virtualenv: /opt/my-toolbox
    virtualenv_command: python3 -m venv
```
Binary: `/opt/my-toolbox/bin/my-toolbox-mcp`.
