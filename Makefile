.PHONY: build test install clean upload check

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
SRC = my_toolbox/*.py tests/*.py  # Adjust according to your project's structure

# Lint target
lint:
	@$(LINTER) $(SRC) || (echo "Linting failed"; exit 1)

# Run tests using `nox`
test:
	@echo "Running tests with nox..."
	nox

	
# Build the package using `python -m build`
build:
	@echo "Checking for requirements.txt..."
	@if [ ! -f requirements.txt ]; then echo "Error: requirements.txt not found."; exit 1; fi
	@echo "Building the package with build module..."
	$(PIP) install --upgrade build
	$(PYTHON) -m build


# Install the package locally
# Install the package locally with requirements check
install:
	@echo "Checking for requirements.txt..."
	@if [ ! -f requirements.txt ]; then echo "Error: requirements.txt not found."; exit 1; fi
	@echo "Installing the package locally..."
	$(PIP) install -r requirements.txt
	$(PIP) install -e .


# Upload the package using `twine`
upload: build
	@echo "Uploading the package with twine..."
	$(PYTHON) -m twine upload dist/*

# Check the package before uploading using `twine check`
check:
	@echo "Checking the package with twine..."
	$(PYTHON) -m twine check dist/*

# Clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf dist/ build/ *.egg-info
