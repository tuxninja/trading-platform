#!/bin/bash

# Trading Platform Startup Script
echo "🚀 Starting Trading Platform..."

# Function to check if port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# Create environment files if they don't exist
echo "📝 Checking environment configuration..."

if [ ! -f backend/.env ]; then
    echo "⚠️  Creating backend .env from template..."
    cp backend/.env.example backend/.env
    echo "📝 Please edit backend/.env with your Google Client ID and JWT secret"
fi

if [ ! -f frontend/.env.local ]; then
    echo "⚠️  Creating frontend .env.local from template..."
    cp frontend/.env.example frontend/.env.local
    echo "📝 Please edit frontend/.env.local with your Google Client ID"
fi

# Start backend
echo "🔧 Starting backend..."
cd backend
source venv/bin/activate

# Find available port for backend
BACKEND_PORT=8000
while check_port $BACKEND_PORT; do
    BACKEND_PORT=$((BACKEND_PORT + 1))
done

echo "🌐 Backend will run on port $BACKEND_PORT"
python main.py --port $BACKEND_PORT &
BACKEND_PID=$!

cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend..."
cd frontend

# Update API URL if backend port changed
if [ $BACKEND_PORT -ne 8000 ]; then
    echo "REACT_APP_API_URL=http://localhost:$BACKEND_PORT" >> .env.local
fi

npm start &
FRONTEND_PID=$!

echo ""
echo "✅ Trading Platform is starting!"
echo "📊 Backend API: http://localhost:$BACKEND_PORT"
echo "🌐 Frontend: http://localhost:3000"
echo ""
echo "⚠️  IMPORTANT: Configure your Google OAuth credentials in the .env files"
echo ""
echo "To stop the platform:"
echo "kill $BACKEND_PID $FRONTEND_PID"

# Wait for user input to stop
read -p "Press Enter to stop the platform..."

# Stop services
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
echo "🛑 Trading Platform stopped."
