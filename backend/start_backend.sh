#!/bin/bash

# Trading Backend Startup Script
echo "🚀 Starting Trading Sentiment Analysis Backend..."

# Kill any existing backend processes
echo "🛑 Stopping any existing backend processes..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "uvicorn.*main" 2>/dev/null || true
sleep 2

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   cd /Users/jasonriedel/PyCharmProjects/Trading/backend"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys if needed"
fi

# Run syntax check
echo "🔍 Checking syntax..."
python -c "import main; print('✅ Syntax check passed')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Syntax error detected. Please check the code."
    exit 1
fi

echo "✅ All checks passed!"
echo "🌐 Starting server at http://localhost:8000"
echo "📊 API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python main.py