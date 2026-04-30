# Package Preparation And Reuse Guide

This project is now configured as a reusable Python package using [pyproject.toml](../pyproject.toml).

## 1. One-time package preparation

1. Ensure package folder has an __init__.py file.
2. Keep project metadata and dependencies in pyproject.toml.
3. Keep runtime dependencies in requirements.txt for local development convenience.
4. Build distributables:

```bash
python -m build
```

Expected artifacts in dist/:

- my_toolbox-<version>-py3-none-any.whl
- my_toolbox-<version>.tar.gz

## 2. Use package in your other projects (pip workflow)

### Option A: Install directly from local source

```bash
pip install /absolute/path/to/My_Toolbox
```

### Option B: Install from built wheel (recommended for stable usage)

```bash
pip install /absolute/path/to/My_Toolbox/dist/my_toolbox-1.1.0-py3-none-any.whl
```

### Option C: Install from GitHub

```bash
pip install "git+https://github.com/Karthick-840/My_Toolbox.git@main"
```

## 3. Use package in your other projects (uv workflow)

If uv is installed in your target project:

### Option A: Add local package dependency

```bash
uv add /absolute/path/to/My_Toolbox
```

### Option B: Add editable local dependency while developing both repos

```bash
uv add --editable /absolute/path/to/My_Toolbox
```

### Option C: Add from GitHub

```bash
uv add "git+https://github.com/Karthick-840/My_Toolbox.git@main"
```

## 4. Version and release process

1. Update version in pyproject.toml.
2. Rebuild artifacts:

```bash
python -m build
```

3. Validate install in a clean environment:

```bash
python -m venv .venv-test
. .venv-test/bin/activate
pip install dist/my_toolbox-<version>-py3-none-any.whl
python -c "import my_toolbox; print('import ok')"
```

4. Commit and tag:

```bash
git add pyproject.toml README.md docs/Package_Preparation.md
git commit -m "Prepare package for reuse"
git tag v<version>
```

## 5. Minimal usage check in a consumer project

```python
from my_toolbox import log_calls

@log_calls(logfile=None)
def ping(name):
    return f"hello {name}"

print(ping("team"))
```

## 6. Notes on optional/runtime integrations

- GCP and Streamlit helpers depend on external packages and service configuration.
- Some modules require credentials or runtime context and may not execute fully without setup.
- Base package import should work after installation.
