#!/bin/bash
"""
Remote deployment script for your Docker host
Run this script on your Docker host to deploy the complete solution
"""

set -e

echo "🚀 KEATchen Customer Monitor - Remote Deployment"
echo "=============================================="
echo "This will deploy the complete customer monitoring solution"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Clone or update repository
if [ -d "keatchen-customer-scraper" ]; then
    echo "📁 Repository exists - updating..."
    cd keatchen-customer-scraper
    git pull origin master
else
    echo "📁 Cloning repository..."
    git clone https://github.com/coder-r/keatchen-customer-scraper.git
    cd keatchen-customer-scraper
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📋 Created .env file - configuring with KEATchen credentials..."
    
    # Update with correct credentials
    sed -i 's/KEATCHEN_USERNAME=admin@keatchen/KEATCHEN_USERNAME=admin@keatchen/' .env
    sed -i 's/KEATCHEN_PASSWORD=keatchen22/KEATCHEN_PASSWORD=keatchen22/' .env
    sed -i 's/HEADLESS=true/HEADLESS=true/' .env
    
    echo "✅ Environment configured"
fi

# Create data directories
mkdir -p data logs

echo "🔨 Building Docker containers..."

# Build containers
docker build -t keatchen-monitor:latest .
docker build -f Dockerfile.dashboard -t keatchen-dashboard:latest .

echo "✅ Containers built successfully"

# Initialize database with existing customers
echo "🗄️ Initializing database with existing customers..."
python3 init_database.py

echo "🚀 Starting KEATchen Customer Monitor..."

# Start services
docker-compose up -d

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================="
echo ""
echo "📊 Dashboard:    http://localhost:8081"
echo "🔍 Monitor Logs: docker-compose logs -f keatchen-monitor"
echo "📈 Dashboard:    docker-compose logs -f keatchen-dashboard"
echo ""
echo "📂 Data Directory: ./data/"
echo "📝 Logs Directory: ./logs/"
echo ""
echo "🔧 Management Commands:"
echo "  View Status:  docker-compose ps"
echo "  Stop Service: docker-compose down"
echo "  Restart:      docker-compose restart"
echo "  View Logs:    docker-compose logs -f"
echo ""
echo "⏰ The system will now:"
echo "  ✅ Monitor for new customers every hour"
echo "  ✅ Extract missing customers from pages 14-19, 21-24"
echo "  ✅ Alert you about new customer registrations"
echo "  ✅ Maintain complete customer database"
echo ""
echo "🎯 Expected: ~530+ customers after first complete scan"