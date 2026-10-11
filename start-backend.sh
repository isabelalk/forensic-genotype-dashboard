#!/bin/bash

echo "🚀 Starting Backend Server on port 3002..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 3002
