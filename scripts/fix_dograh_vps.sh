#!/bin/bash
# ============================================
# FIX DOGRAH VPS - Nginx + TURN Configuration
# Run on your Contabo VPS: ssh root@147.93.169.183
# Then: bash fix_dograh_vps.sh
# ============================================

set -e

DOMAIN="voice.city-maps.online"
VPS_IP="147.93.169.183"

echo "=== Dograh VPS Fix Script ==="
echo "Domain: $DOMAIN"
echo "IP: $VPS_IP"
echo ""

# Step 1: Fix nginx configuration
echo "[1/4] Fixing nginx configuration..."

# Backup existing config
if [ -f /etc/nginx/sites-available/dograh ]; then
    cp /etc/nginx/sites-available/dograh /etc/nginx/sites-available/dograh.bak
    echo "  Backed up existing config"
fi

# Write correct nginx config
cat > /etc/nginx/sites-available/dograh << 'NGINX_CONF'
upstream dograh_api {
    server 127.0.0.1:8000;
}

upstream dograh_ui {
    server 127.0.0.1:3010;
}

server {
    listen 80;
    server_name voice.city-maps.online;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name voice.city-maps.online;

    ssl_certificate /root/dograh/certs/local.crt;
    ssl_certificate_key /root/dograh/certs/local.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # API routes -> backend (port 8000)
    location /api/ {
        proxy_pass http://dograh_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # WebSocket for real-time audio
    location /ws/ {
        proxy_pass http://dograh_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Everything else -> UI (port 3010)
    location / {
        proxy_pass http://dograh_ui;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX_CONF

# Enable the site
ln -sf /etc/nginx/sites-available/dograh /etc/nginx/sites-enabled/dograh

# Remove default if it conflicts
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default
    echo "  Removed default nginx site"
fi

# Test nginx config
echo "  Testing nginx config..."
nginx -t

# Reload nginx
systemctl reload nginx
echo "  Nginx reloaded successfully!"
echo ""

# Step 2: Fix SSL certificate (use Let's Encrypt if certbot available)
echo "[2/4] Checking SSL certificate..."
if command -v certbot &> /dev/null; then
    echo "  Certbot found. Getting proper SSL cert..."
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@citymaps.online --redirect 2>/dev/null || echo "  Certbot failed - using self-signed cert (browser will show warning)"
else
    echo "  Certbot not found. Install with: apt install certbot python3-certbot-nginx"
    echo "  Then run: certbot --nginx -d $DOMAIN"
    echo "  Using self-signed cert for now (browser will show security warning)"
fi
echo ""

# Step 3: Enable TURN server for WebRTC audio
echo "[3/4] Checking TURN server configuration..."
cd /root/dograh 2>/dev/null || cd ~/dograh 2>/dev/null || echo "  WARNING: dograh directory not found at /root/dograh"

if [ -f .env ]; then
    # Check if TURN is configured
    if grep -q "TURN_ENABLED=false" .env 2>/dev/null || ! grep -q "TURN_ENABLED" .env 2>/dev/null; then
        echo "  TURN is disabled. Enabling..."
        # Update or add TURN settings
        if grep -q "TURN_ENABLED" .env; then
            sed -i 's/TURN_ENABLED=false/TURN_ENABLED=true/' .env
        else
            echo "" >> .env
            echo "# TURN Server for WebRTC" >> .env
            echo "TURN_ENABLED=true" >> .env
            echo "TURN_SERVER_URL=turn:${VPS_IP}:3478" >> .env
            echo "TURN_SERVER_USERNAME=dograh" >> .env
            echo "TURN_SERVER_PASSWORD=dograh_turn_2024" >> .env
        fi
        echo "  TURN enabled in .env"
    else
        echo "  TURN already enabled"
    fi
else
    echo "  WARNING: .env not found in dograh directory"
fi
echo ""

# Step 4: Restart Dograh services
echo "[4/4] Restarting Dograh services..."
if [ -f docker-compose.yaml ] || [ -f docker-compose.yml ]; then
    docker compose --profile remote down 2>/dev/null || docker compose down
    docker compose --profile remote up -d 2>/dev/null || docker compose up -d
    echo "  Dograh services restarted!"
else
    echo "  WARNING: No docker-compose file found. Restart manually."
fi
echo ""

# Step 5: Open firewall ports for WebRTC
echo "[BONUS] Checking firewall ports for WebRTC..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp 2>/dev/null
    ufw allow 443/tcp 2>/dev/null
    ufw allow 3478/tcp 2>/dev/null
    ufw allow 3478/udp 2>/dev/null
    ufw allow 5349/tcp 2>/dev/null
    ufw allow 5349/udp 2>/dev/null
    ufw allow 49152:49200/udp 2>/dev/null
    echo "  UFW ports opened"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp 2>/dev/null
    firewall-cmd --permanent --add-port=443/tcp 2>/dev/null
    firewall-cmd --permanent --add-port=3478/tcp 2>/dev/null
    firewall-cmd --permanent --add-port=3478/udp 2>/dev/null
    firewall-cmd --permanent --add-port=5349/tcp 2>/dev/null
    firewall-cmd --permanent --add-port=5349/udp 2>/dev/null
    firewall-cmd --permanent --add-port=49152-49200/udp 2>/dev/null
    firewall-cmd --reload 2>/dev/null
    echo "  Firewalld ports opened"
else
    echo "  No firewall tool found. Ensure these ports are open in Contabo panel:"
    echo "  TCP: 80, 443, 3478, 5349"
    echo "  UDP: 3478, 5349, 49152-49200"
fi
echo ""

echo "=== DONE ==="
echo ""
echo "Now test:"
echo "  1. Open https://$DOMAIN in browser (accept cert warning if self-signed)"
echo "  2. Login with: admin@citymaps.online / CityMaps2024!"
echo "  3. Go to Telephony Configurations and verify Vobiz is set up"
echo "  4. Test a call from the Dograh UI"
echo ""
echo "If login still redirects, clear browser cookies for $DOMAIN and try again."
