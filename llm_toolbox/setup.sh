#!/bin/bash

# Ensure system is updated
sudo apt-get update

# Install SQLite system packages
sudo apt-get install -y sqlite3 libsqlite3-dev

# Install Python 3 venv (if not installed)
sudo apt-get install -y python3-venv

# Set up the virtual environment
python3 -m venv llm_venv

# Activate the virtual environment
source llm_venv/bin/activate

# Install the Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup completed successfully!"
