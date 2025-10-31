#!/bin/bash

# NLP Processing Pipeline Startup Script

echo "======================================"
echo "NLP Processing Pipeline Setup"
echo "======================================"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment (optional)
read -p "Create virtual environment? (y/n): " create_venv
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv nlp_env
    source nlp_env/bin/activate
    echo "Virtual environment activated"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Download spaCy models
echo ""
echo "Downloading spaCy models..."
python -m spacy download en_core_web_sm

if [ $? -ne 0 ]; then
    echo "⚠️ Warning: Failed to download spaCy model. You can download it manually later."
fi

# Run tests
echo ""
echo "Running tests..."
python test_pipeline.py

if [ $? -ne 0 ];
then
    echo "⚠️ Some tests failed. Check the output above."
fi

# Start server
echo ""
echo "======================================"
echo "Starting NLP Pipeline Server..."
echo "======================================"
echo ""
echo "Server will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py
