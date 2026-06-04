# AI Employee Automation Platform

A production-grade multi-agent AI system that autonomously discovers businesses, analyzes their web presence, generates demo websites, performs outreach, manages follow-ups, and scales into a full AI-powered digital agency.

## Architecture

```
+-----------------------------------------------------------+
|                  Frontend (Next.js + Tailwind)              |
|              CRM Dashboard / Lead Management               |
+-----------------------------+-----------------------------+
                              | REST API
+-----------------------------v-----------------------------+
|                   Backend (FastAPI + Python)               |
|  +----------+ +----------+ +----------+ +----------+     |
|  | Lead     | | Analysis | | Website  | | Outreach |     |
|  | Discovery| | Agent    | | Gen Agent| | Agent    |     |
|  +----------+ +----------+ +----------+ +----------+     |
|         CrewAI Orchestration + LangGraph State            |
+------+---------------+---------------+-------------------+
       |               |               |
  +----v----+    +----v----+    +-----v-----+
  | Supabase|    |  Redis  |    |    n8n    |
  |   DB    |    | + Celery|    | Workflows |
  +---------+    +---------+    +-----------+
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind CSS, TypeScript, Recharts |
| Backend | FastAPI, Python 3.11 |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth |
| LLM | OpenRouter (Claude, GPT-4, etc.) |
| Agents | CrewAI, LangGraph |
| Automation | n8n (workflow engine) |
| Scraping | Browser Use |
| Queue | Celery + Redis |
| Hosting | Docker, Vercel (frontend) |

## Quick Start

```bash
cd ai-agency-platform
cp .env.example .env
# Fill in your credentials in .env

# Run the Supabase schema (copy scripts/supabase-schema.sql into Supabase SQL Editor)

# Start everything
docker compose up -d
```

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | CRM Dashboard |
| Backend | http://localhost:8000 | API + AI Agents |
| API Docs | http://localhost:8000/docs | Swagger UI |
| n8n | http://localhost:5678 | Workflow Automation |
| Redis | localhost:6379 | Task Queue + Cache |

## API Endpoints

### Leads
- `GET /api/leads/` - List leads (filter by status)
- `POST /api/leads/` - Create lead manually
- `POST /api/leads/discover?location=X&category=Y` - AI discovery
- `POST /api/leads/{id}/analyze` - Run website analysis

### Websites
- `POST /api/websites/generate?lead_id=X&template=Y` - Generate AI website
- `GET /api/websites/lead/{lead_id}` - Get websites for lead
- `POST /api/websites/{id}/deploy` - Deploy approved website

### Outreach
- `POST /api/outreach/send?lead_id=X&channel=email` - Send outreach
- `POST /api/outreach/followup/{lead_id}` - Trigger follow-up
- `GET /api/outreach/lead/{lead_id}` - Message history

### Dashboard
- `GET /api/dashboard/stats` - Platform statistics
- `GET /api/dashboard/activity` - Agent activity logs

## Project Structure

```
ai-agency-platform/
+-- backend/
|   +-- app/
|   |   +-- agents/              # AI agent definitions
|   |   |   +-- lead_discovery/  # Google Maps scraping agent
|   |   |   +-- website_analysis/# Website scoring agent
|   |   |   +-- website_generation/# AI website builder
|   |   |   +-- outreach/       # Message generation agent
|   |   |   +-- followup/       # Follow-up automation
|   |   |   +-- deployment/     # Website deployment agent
|   |   +-- api/routes/         # FastAPI endpoints
|   |   +-- core/               # Config, DB, LLM, logging
|   |   +-- schemas/            # Pydantic models
|   |   +-- services/           # Business logic layer
|   |   +-- workers/            # Celery background tasks
|   +-- Dockerfile
|   +-- requirements.txt
+-- frontend/
|   +-- src/
|   |   +-- app/                # Next.js pages
|   |   +-- components/         # React components
|   |   +-- lib/                # API client, utilities
|   +-- Dockerfile
|   +-- package.json
+-- n8n-workflows/              # Importable workflow JSONs
+-- scripts/
|   +-- setup.sh
|   +-- supabase-schema.sql
+-- docker-compose.yml
+-- .env.example
```

## Core Frameworks (Dependencies)

| Framework | Role | Install Method |
|-----------|------|---------------|
| CrewAI | Multi-agent orchestration | pip (requirements.txt) |
| n8n | Workflow automation | Docker container |
| Browser Use | Web scraping | pip (requirements.txt) |
| LangGraph | Stateful agent memory | pip (requirements.txt) |
| OpenHands | Autonomous coding (Phase 2) | Separate service |

## Development Phases

### Phase 1 (MVP)
- [x] Supabase schema and integration
- [x] Lead CRUD + AI discovery
- [x] Website analysis agent
- [x] Website generation agent
- [x] Outreach agent with AI messaging
- [x] Follow-up automation
- [x] CRM Dashboard
- [x] Docker setup
- [x] n8n workflow templates
- [x] Celery background workers

### Phase 2
- [ ] Browser Use integration for real Google Maps scraping
- [ ] OpenHands integration for full website code generation
- [ ] Multi-channel outreach (WhatsApp Business API)
- [ ] Advanced follow-up sequences
- [ ] LangGraph persistent memory across sessions

### Phase 3
- [ ] Self-improving agent workflows
- [ ] A/B testing outreach messages
- [ ] Automated deployment pipeline (Vercel/Netlify)
- [ ] Multi-tenant support
- [ ] Billing and payment integration

## Environment Variables

See `.env.example` for all required configuration.

## License

MIT
