#!/bin/bash

# HunterMatrix Intelligent Security Platform Startup Script
# Author: HunterMatrix Team
# Version: 1.0
# Description: Start HunterMatrix Web Interface Server

echo "🚀 Starting HunterMatrix Intelligent Security Platform..."
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 not found, please install Python3 first"
    exit 1
fi

# Check if port 8083 is occupied
if lsof -Pi :8083 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Warning: Port 8083 is already in use"
    echo "Attempting to stop existing service..."
    pkill -f "python3 -m http.server 8083" 2>/dev/null || true
    sleep 2
fi

# Switch to web-ui directory
cd "$(dirname "$0")/web-ui" || {
    echo "❌ Error: Cannot find web-ui directory"
    exit 1
}

# Check if huntermatrix_final.html exists
if [ ! -f "huntermatrix_final.html" ]; then
    echo "❌ Error: huntermatrix_final.html file not found"
    exit 1
fi

echo "📁 Working directory: $(pwd)"
echo "🌐 Starting HTTP server..."
echo "📡 Listening port: 8083"
echo "🔗 Access URL: http://localhost:8083/huntermatrix_final.html"
echo "======================================"
echo "✅ Server started successfully!"
echo "💡 Tip: Press Ctrl+C to stop the server"
echo "🌐 Opening browser automatically..."
echo ""

# StartHTTPService器
python3 -m http.server 8083 &
SERVER_PID=$!

# 等待Service器Start
sleep 2

# Automatic打开浏览器（macOS）
if command -v open &> /dev/null; then
    open "http://localhost:8083/huntermatrix_final.html"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "http://localhost:8083/huntermatrix_final.html"
elif command -v start &> /dev/null; then
    # Windows
    start "http://localhost:8083/huntermatrix_final.html"
fi

# Wait for user interruption
trap "echo ''; echo '🛑 Stopping server...'; kill $SERVER_PID 2>/dev/null; echo '✅ Server stopped'; exit 0" INT

# Keep script running
wait $SERVER_PID
