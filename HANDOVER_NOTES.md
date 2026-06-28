# City Maps Platform - Complete Handover Notes
Last Updated: June 28 2026
For use on new laptop with any AI coding agent

---

## 1. WHAT IS THIS PROJECT?

City Maps is a digital growth platform for local Indian businesses.
- Admin sells websites + digital marketing to local businesses
- Each business gets subdomain: businessname.city-maps.online
- Pricing: Rs.29/month (Growth) | Rs.39/month (Premium)

---

## 2. LIVE URLS

Main Website: https://city-maps.online
Admin Dashboard: https://ai-agency-platform-blush.vercel.app
Backend API: https://ai-agency-platform.onrender.com
API Docs: https://ai-agency-platform.onrender.com/docs
Voice Agent VPS: https://voice.city-maps.online
Voice Blast: https://ai-agency-platform.onrender.com/api/admin/voice-blast?pwd=kalpdev2024
Admin Panel: https://ai-agency-platform.onrender.com/api/admin/manage?pwd=kalpdev2024
Voice Calls: https://ai-agency-platform.onrender.com/api/admin/voice-calls?pwd=kalpdev2024
All Sites: https://ai-agency-platform.onrender.com/api/sites
Ads Manager: https://ai-agency-platform.onrender.com/api/ads/manage?pwd=kalpdev2024
QA Agent: https://ai-agency-platform.onrender.com/api/qa/review-all
GitHub: https://github.com/sjaiswal210-beep/ai-agency-platform

Admin password: kalpdev2024

---

## 3. TECH STACK

Frontend: Next.js 14, Tailwind CSS, TypeScript
Backend: FastAPI, Python 3.11
Database: Supabase (PostgreSQL)
LLM: Gemini Flash (Google)
Voice: Vobiz (calls) + Sarvam AI (TTS)
WhatsApp: Meta Cloud API (Phone ID: 1202589086266794)
DNS: Cloudflare (wildcard *.city-maps.online)
Frontend Hosting: Vercel (auto-deploy from GitHub)
Backend Hosting: Render (auto-deploy from GitHub)
Voice VPS: Contabo (IP: 147.93.169.183)

---

## 4. FOLDER STRUCTURE

ai-agency-platform/
  backend/
    app/main.py           <- Entry point
    app/api/routes/       <- All API endpoints
    app/modules/          <- Voice, WhatsApp, etc.
    requirements.txt
    .env                  <- COPY THIS
  frontend/src/app/
    page.tsx              <- Main Admin Dashboard
    admin/                <- Admin Portal
    dashboard/[orgSlug]/  <- Business client dashboard
      crm/               <- CRM module
      billing/            <- Billing module
      booking/            <- Booking module
    leads/                <- Lead management
    websites/             <- Website management
    analytics/ outreach/ tools/ growth/ notes/ creatives/ editor/

---

## 5. ENV VARIABLES

Backend (Render): SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY,
GOOGLE_PLACES_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
WHATSAPP_TOKEN (PENDING permanent token), WHATSAPP_PHONE_ID=1202589086266794,
ENCRYPTION_KEY, VOBIZ_AUTH_ID, VOBIZ_AUTH_TOKEN, SARVAM_API_KEY, DEEPGRAM_API_KEY

Frontend (Vercel): NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY,
NEXT_PUBLIC_API_URL=https://ai-agency-platform.onrender.com

Copy .env files: ai-agency-platform/.env and ai-agency-platform/backend/.env

---

## 6. KEY FEATURES BUILT

ADMIN DASHBOARD (/)
- Stats: total leads, contacted, converted, sites generated
- Quick Actions: New Campaign, Voice Blast, Discover, Find Business, Scrape Area
- Pipeline status + recent leads

LEAD DISCOVERY
- Discover: Google Maps by location + category
- Find Business: by name + pincode, auto-creates website
- Scrape Area: ALL businesses in area, AI auto-categorizes

WEBSITE GENERATION
- AI builds website from Google business data
- Hosted at: {slug}.city-maps.online

WHATSAPP OUTREACH
- Personalized messages via Meta Cloud API
- PENDING: Need permanent token from Meta Business Manager

VOICE BLAST
- Script -> Sarvam TTS -> MP3 -> Vobiz dials -> plays audio
- Cost: Rs.0.50/call

BUSINESS DASHBOARD (/dashboard/[orgSlug]/)
- Each client has own dashboard with only their enabled modules
- Modules: CRM, Billing, Booking, Website, WhatsApp, Analytics, AI Employee

CRM MODULE (/dashboard/[orgSlug]/crm)
- Contacts: leads, customers, vendors, partners, employees
- Pipeline: new -> contacted -> qualified -> proposal -> won -> lost
- Activity timeline: calls, meetings, notes, WhatsApp, email, tasks

ADMIN PORTAL (/admin)
- Manage all organizations, toggle modules, apply templates, create orgs

---

## 7. PENDING ITEMS

1. WhatsApp permanent token (get from Meta Business Manager)
2. Razorpay payment integration for subscriptions
4. Phase 2: Browser Use scraping, OpenHands code gen, LangGraph memory

---

## 8. IMPORTANT RULES

- NEVER use AI in customer-facing content. Use automation/smart/digital
- Admin password: kalpdev2024
- All frontend pages have: const API_BASE = https://ai-agency-platform.onrender.com
- Business sites format: {slug}.city-maps.online
- Cloudflare wildcard DNS handles *.city-maps.online

---

## 9. SETUP ON NEW LAPTOP

1. git clone https://github.com/sjaiswal210-beep/ai-agency-platform.git
2. Copy .env files from old laptop
3. cd frontend then npm install then npm run dev
4. Backend (optional): cd backend then pip install -r requirements.txt
   then uvicorn app.main:app --reload --port 8000
5. Or just use production - auto-deploys on git push to main
6. SSH Voice VPS: ssh root@147.93.169.183

---

## 10. SUPABASE KEY TABLES

organizations, organization_modules, modules
leads, websites, outreach_messages
crm_contacts, crm_activities, voice_calls

---

## 11. CONTEXT PROMPT FOR NEW AI AGENT

Paste this when starting fresh:

I am working on City Maps - a digital agency platform for local Indian
businesses. Backend: FastAPI on Render (https://ai-agency-platform.onrender.com).
Frontend: Next.js 14 on Vercel (https://ai-agency-platform-blush.vercel.app).
Database: Supabase PostgreSQL.
GitHub: sjaiswal210-beep/ai-agency-platform.
Admin password: kalpdev2024.
Business sites: {slug}.city-maps.online.
All frontend pages use: const API_BASE = https://ai-agency-platform.onrender.com
Do NOT say AI in customer content - use automation/smart/digital.
Pricing: Rs.29/month Growth, Rs.39/month Premium.
Features: Lead discovery (Google Maps), website generation, WhatsApp outreach,
Voice blast, CRM per business, Admin module control.
Pending: WhatsApp permanent token, Razorpay payments.
See HANDOVER_NOTES.md for full details.

---
Generated: June 28, 2026
