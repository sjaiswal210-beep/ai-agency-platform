#!/bin/bash
set -e

echo "==================================="
echo " AI Agency Platform Setup"
echo "==================================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required. Install: https://docs.docker.com/get-docker/"; exit 1; }
command -v docker compose >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose required"; exit 1; }

# Create .env from example if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "Created .env from .env.example"
    echo "Please fill in your credentials:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_SERVICE_KEY"
    echo "  - SUPABASE_ANON_KEY"
    echo "  - OPENROUTER_API_KEY"
    echo ""
    echo "Then run this script again."
    exit 0
fi

# Build and start services
echo ""
echo "Building Docker containers..."
docker compose build

echo ""
echo "Starting services..."
docker compose up -d

echo ""
echo "==================================="
echo " Platform is running"
echo "==================================="
echo ""
echo "  Frontend:   http://localhost:3000"
echo "  Backend:    http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  n8n:        http://localhost:5678"
echo ""
echo "Next steps:"
echo "  1. Run scripts/supabase-schema.sql in Supabase SQL Editor"
echo "  2. Import n8n-workflows/*.json into n8n"
echo "  3. Start discovering leads from the dashboard"
echo ""
