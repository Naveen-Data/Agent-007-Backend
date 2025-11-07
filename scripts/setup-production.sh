#!/bin/bash

# Production environment setup script for EC2
# Run this after SSH-ing into your EC2 instance

set -e

echo "🔧 Setting up Agent 007 Backend production environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on EC2
if ! curl -s http://169.254.169.254/latest/meta-data/instance-id &> /dev/null; then
    echo_error "This script should be run on an EC2 instance"
    exit 1
fi

cd /home/ec2-user/app/Agent_007_Backend

# Create production .env file
echo_info "Creating production environment configuration..."

cat > .env << EOF
# Production Environment Variables for Agent 007 Backend

# Google Gemini API (REQUIRED - Update with your actual key)
GOOGLE_API_KEY=your_actual_gemini_api_key_here
GEMINI_DEFAULT_MODEL=gemini-2.5-flash-lite
GEMINI_HEAVY_MODEL=gemini-2.5-pro
EMBEDDING_MODEL=gemini-embedding-001

# LangSmith (Optional - for monitoring and tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_PROJECT=agent_007_production

# Server Configuration
BACKEND_PORT=8000
ALLOWED_ORIGINS=*

# Vector Database
CHROMA_DIR=./chroma_db
CHROMA_TELEMETRY_ENABLED=false

# AWS Configuration (automatically detected)
AWS_REGION=us-east-1
EOF

echo_warning "⚠️  IMPORTANT: You must update the .env file with your actual API keys!"
echo_info "Edit the file: nano .env"
echo_info "Required: GOOGLE_API_KEY (get from: https://makersuite.google.com/app/apikey)"

# Create update script
cat > update.sh << 'EOF'
#!/bin/bash
echo "🔄 Updating Agent 007 Backend..."

# Pull latest changes
git pull origin main

# Stop container
docker stop agent-007-backend

# Remove old container
docker rm agent-007-backend

# Rebuild image
docker build -t agent-007-backend .

# Start new container
docker run -d \
    --name agent-007-backend \
    --restart unless-stopped \
    -p 8000:8000 \
    --env-file .env \
    agent-007-backend

echo "✅ Update complete!"
echo "Check logs: docker logs agent-007-backend"
EOF

chmod +x update.sh

# Create maintenance scripts
cat > logs.sh << 'EOF'
#!/bin/bash
echo "📋 Agent 007 Backend Logs:"
docker logs agent-007-backend --tail 50 -f
EOF

cat > status.sh << 'EOF'
#!/bin/bash
echo "📊 Agent 007 Backend Status:"
echo "Container Status:"
docker ps | grep agent-007-backend

echo ""
echo "Health Check:"
curl -s http://localhost:8000/health || echo "❌ Health check failed"

echo ""
echo "System Resources:"
free -h
df -h / | tail -1
EOF

chmod +x logs.sh status.sh

echo_info "✅ Production environment setup complete!"
echo_info ""
echo_info "Next steps:"
echo_info "1. Edit .env with your API keys: nano .env"
echo_info "2. Restart the application: ./update.sh"
echo_info "3. Check logs: ./logs.sh"
echo_info "4. Monitor status: ./status.sh"
echo_info ""
echo_info "Your backend will be available at:"
echo_info "http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"