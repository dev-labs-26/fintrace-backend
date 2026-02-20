#!/bin/bash

# Fintrace Backend - Local Development Startup Script

echo "🚀 Starting Fintrace Backend..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Set default port if not specified
export PORT=${PORT:-8000}

# Start the server
echo "✅ Starting server on port $PORT..."
echo "📚 API Documentation: http://localhost:$PORT/docs"
echo "🏥 Health Check: http://localhost:$PORT/health"
echo ""

uvicorn main:app --host 0.0.0.0 --port $PORT --reload
