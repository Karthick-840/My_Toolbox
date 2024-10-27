.PHONY: build test install clean

# Define variables
PACKAGE_NAME = My_Toolbox
SRC_DIR = My_Toolbox
TEST_DIR = tests

# Detect OS
OS := $(shell uname)

# Define Python and pip commands based on OS
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

# Build the package using setup.py
build-setup: setup.py
	@echo "Building the package using setup.py..."
	$(PYTHON) setup.py sdist bdist_wheel

# Run tests
test:
	@echo "Running tests..."
	$(PYTHON) $(TEST_DIR)/run_tests.py

# Install the package locally
install:
	@echo "Installing the package locally..."
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

# Clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf dist/ build/ *.egg-info
