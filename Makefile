.PHONY: build test install clean upload check app ruff lint export-prod

# Define your Python interpreter
PYTHON = python3
PACKAGE_NAME = my_toolbox
SRC_DIR = my_toolbox
TEST_DIR = tests
LINTER = pylint
# Detect OS and define Python and pip commands based on OS

OS := $(shell uname)
ifeq ($(OS),Linux)
    PYTHON = python3
    PIP = pip3
else ifeq ($(OS),Darwin) # macOS
    PYTHON = python3
    PIP = pip3
else ifeq ($(OS),Windows_NT)
    PYTHON = python
    PIP = pip
else
    $(error Unsupported OS)
endif

# Define the source files or directories to lint
SRC = my_toolbox/*/*.py tests/*.py  # Adjust according to your project's structure

# Lint target
lint:
	@echo "Linting the following files:"
	@echo $(SRC)
	@$(LINTER) --exit-zero --output-format=text $(SRC) | tee pylint_report.txt
	@echo "Pylint score for each file:"
	@grep -E "Your code has been rated at" pylint_report.txt
	@awk '/Your code has been rated at/ { split($$7, score, "/"); if (score[1] < 2.5) { exit 1 } else if (score[1] < 8) { exit 2 } }' pylint_report.txt || \
		{ if [ $$? -eq 1 ]; then echo "Linting failed: Pylint score is less than 2.5"; exit 1; \
		elif [ $$? -eq 2 ]; then echo "Linting warning: Pylint score is between 2.5 and 8"; exit 0; \
		else echo "Linting success: Pylint score is 8 or higher"; fi; }

# Run tests (dev group + all extras, locked by uv.lock)
test:
	uv run --all-extras pytest

# Run ruff
ruff:
	uv run ruff check my_toolbox app tests

# Run the local PDF Operations app
app:
	uv run --extra documents --group app python -m app.pdf_app

# Build the package (sdist + wheel)
build:
	uv build

# Install the package + all extras into the local uv environment
install:
	uv sync --all-extras

# Upload the package using `twine`
upload: build
	uv run --group release twine upload dist/*

# Check the package before uploading using `twine check`
check:
	uv run --group release twine check dist/*

# Export pinned production requirements (for deployment targets that need requirements.txt)
export-prod:
	uv export --no-dev --extra all --no-emit-project --no-hashes

# Clean up build artifacts
clean:
	rm -rf dist/ build/ *.egg-info
