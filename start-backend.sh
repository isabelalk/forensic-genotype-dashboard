#!/bin/bash

echo "🚀 Starting Backend Server on port 3002..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 3002
