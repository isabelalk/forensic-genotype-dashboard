#!/bin/bash

echo "Starting HIrisPlex-S + PLEX-34 development environment"
echo ""

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "pnpm is not installed. Installing globally with npm..."
    npm install -g pnpm
fi

# Check if Python venv exists
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    pnpm install
    cd ..
fi

echo ""
echo "All dependencies installed."
echo ""
echo "Starting services..."
echo ""
echo "Backend will be available at: http://localhost:3002"
echo "Backend API docs at: http://localhost:3002/docs"
echo "Frontend will be available at: http://localhost:5173"
echo ""

# Start both services
pnpm dev
