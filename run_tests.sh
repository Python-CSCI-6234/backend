#!/bin/bash

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install test dependencies
pip install -r requirements.txt

# Set test environment
export ENV_FILE=.env.test

# Run tests with coverage
pytest tests/ --cov=main --cov=auth --cov=services --cov-report=term-missing

# Deactivate virtual environment
deactivate 