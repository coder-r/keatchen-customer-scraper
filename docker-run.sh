#!/bin/bash
"""
Production deployment script for KEATchen Customer Monitor
"""

set -e

echo "🚀 KEATchen Customer Monitor - Production Deployment"
echo "=================================================="

# Create necessary directories
mkdir -p data logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📋 Created .env file from template - please configure credentials"
    echo "⚠️  Edit .env file with your KEATchen admin credentials before running"
    exit 1
fi

echo "🔨 Building Docker containers..."

# Build the main monitoring container
docker build -t keatchen-monitor:latest .

# Build the dashboard container
docker build -f Dockerfile.dashboard -t keatchen-dashboard:latest .

echo "✅ Containers built successfully"

echo "🚀 Starting KEATchen Customer Monitor..."

# Start the services
docker-compose up -d

echo "✅ Services started successfully!"
echo ""
echo "📊 Dashboard: http://localhost:8081"
echo "🔍 Monitor logs: docker-compose logs -f keatchen-monitor"
echo "📈 Dashboard logs: docker-compose logs -f keatchen-dashboard"
echo ""
echo "🔧 Management commands:"
echo "  Stop:    docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Logs:    docker-compose logs -f"
echo "  Status:  docker-compose ps"
echo ""
echo "📂 Data location: ./data/"
echo "📝 Logs location: ./logs/"