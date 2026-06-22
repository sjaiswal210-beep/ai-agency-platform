#!/bin/bash
# ============================================
# DOGRAH DEPLOYMENT SCRIPT FOR CITYMAPS
# Run this on your Contabo VPS (Ubuntu 22.04)
# ============================================

echo "=== CityMaps Voice AI - Dograh Deployment ==="
echo ""

# Step 1: Install Docker
echo "[1/5] Installing Docker..."
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Step 2: Install Docker Compose
echo "[2/5] Docker Compose check..."
docker compose version || {
    apt-get update && apt-get install -y docker-compose-plugin
}

# Step 3: Download Dograh
echo "[3/5] Downloading Dograh..."
curl -o docker-compose.yaml https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml
curl -o start_docker.sh https://raw.githubusercontent.com/dograh-hq/dograh/main/scripts/start_docker.sh
chmod +x start_docker.sh

# Step 4: Create .env file
echo "[4/5] Creating environment config..."
cat > .env << 'EOF'
# Dograh Config for CityMaps Voice Calling
OSS_JWT_SECRET=citymaps-dograh-secret-change-this-in-production
POSTGRES_PASSWORD=dograh_secure_2024
REDIS_PASSWORD=dograh_redis_2024
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123secure

# Environment
ENVIRONMENT=local
ENABLE_TELEMETRY=false

# Workers (4 vCPU server = 2-3 workers optimal)
FASTAPI_WORKERS=2
EOF

# Step 5: Start Dograh
echo "[5/5] Starting Dograh (this takes 2-3 minutes on first run)..."
docker compose up -d --pull always

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo ""
echo "Dograh UI: http://$(curl -s ifconfig.me):3010"
echo "Dograh API: http://$(curl -s ifconfig.me):8000"
echo ""
echo "NEXT STEPS:"
echo "1. Open http://YOUR_IP:3010 in browser"
echo "2. Create your first voice agent (paste CityMaps Hindi prompt)"
echo "3. Connect Exotel/Plivo under Telephony"
echo "4. Add Gemini API key under LLM settings"
echo "5. Set webhook: https://ai-agency-platform.onrender.com/api/voice-calling/webhook"
echo ""
echo "To check status: docker compose ps"
echo "To view logs: docker compose logs -f api"