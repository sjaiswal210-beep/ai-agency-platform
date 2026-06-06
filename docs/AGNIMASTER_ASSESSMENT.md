# Project Agnimaster - Platform Assessment Report

**Date:** June 6, 2026  
**Platform:** AI Agency Platform (city-maps.online)  
**Stack:** FastAPI (Python 3.11) + Next.js 14 + Supabase + Gemini AI

---

## 1. EXISTING FEATURES INVENTORY

### Backend (21 API Route Files, 50+ Endpoints)

| Module | Status | Description |
|--------|--------|-------------|
| Lead Discovery | ✅ Working | Google Maps search, auto-categorize, area scrape, specific business find |
| Website Generation | ✅ Working | AI content (Gemini), 15+ industry templates, design systems, competitor research |
| Website Preview | ✅ Working | Full HTML rendering, real Google photos, SEO schema, responsive |
| AI Editor | ✅ Working | Natural language website editing via prompts |
| Logo Generation | ✅ Working | SVG icons + FLUX AI image logos via Replicate |
| Video Generation | ✅ Working | LTX-2-distilled via Replicate, multi-clip stitching |
| WhatsApp Outreach | ✅ Working | AI message generation, wa.me links, bulk outreach |
| Owner Panel | ✅ Working | Category-specific toolkit, business management UI |
| Daily Dashboard | ✅ Working | Daily content, WhatsApp messages, social posts, ad slots |
| Growth Tools | ✅ Working | SEO keywords, Google Ads copy, social calendar, competitor analysis, email sequences, 90-day plan |
| AI Chatbot | ✅ Working | Per-website AI receptionist answering customer questions |
| Social Creatives | ✅ Working | Template-based ad/post generation |
| Site Manager | ✅ Working | Admin dashboard with AI editing, version tracking |
| Client Auth | ⚠️ Structure | Registration/login endpoints exist, no frontend |
| Payments | ⚠️ Structure | Razorpay order creation, needs real keys |
| Deploy | ⚠️ Placeholder | Generates preview URL only |
| Slug-based URLs | ✅ Working | city-maps.online/{business-slug} |
| Automation | ✅ Working | APScheduler: lead pipeline (6h), follow-up (24h) |

### Frontend (9 Pages)

| Page | Purpose |
|------|---------|
| Dashboard | Stats, quick actions, lead discovery, area scrape, WhatsApp outreach |
| Leads | Lead management list |
| Websites | Generated websites grid |
| Outreach | Messaging center |
| Editor | AI-powered website editing |
| Tools | Business toolkit |
| Creatives | Ad/post generation |
| Growth | SEO, ads, social calendar |
| Analytics | Business analytics |
| [slug] | Public website viewer |

### Agents (6 Core Agents)

- Lead Discovery Agent (Google Maps → structured lead data)
- Website Analysis Agent (score 0-100, gap identification)
- Website Generation Agent (full JSON content + auto-logo)
- Outreach Agent (personalized messages)
- Follow-up Agent (48h rule, intelligent timing)
- Deployment Agent (preview URL generation)

---

## 2. ARCHITECTURE ASSESSMENT

### Strengths
- Clean FastAPI structure with proper router separation
- Service layer pattern (LeadService, WebsiteService, etc.)
- Async operations throughout
- Structured logging
- Environment-based configuration (Pydantic Settings)
- APScheduler for background automation
- Good AI prompt engineering (industry-specific, design systems)

### Weaknesses
- **Duplicate router registrations** in main.py (each router included 2x)
- No caching layer (Redis configured but unused)
- No rate limiting on API endpoints
- No proper error handling middleware per-route
- Frontend has hardcoded `localhost:8000` in some components
- No test suite
- No CI/CD pipeline
- preview.py is 700+ lines (monolithic HTML generator)

---

## 3. DATABASE ASSESSMENT

### Current Schema (Supabase PostgreSQL)

| Table | Rows | Purpose | Scalability |
|-------|------|---------|-------------|
| leads | ~100+ | Business profiles | Good (indexed) |
| websites | 97 | Generated website content (JSONB) | Good |
| outreach_messages | - | Email/WhatsApp messages | Good |
| agent_logs | - | AI action audit trail | Good |
| clients | - | Business owner accounts | Phase 2 |
| payments | - | Razorpay transactions | Phase 2 |
| bookings | - | Appointment requests | Phase 2 |

### Missing Tables (for Agnimaster vision)
- `subscriptions` — recurring billing tracking
- `analytics_events` — page views, clicks, leads captured per website
- `seo_reports` — keyword rankings, visibility scores
- `content_versions` — website content version history
- `campaigns` — marketing campaign tracking
- `voice_assets` — voice recordings, narrations
- `growth_metrics` — business outcome tracking

---

## 4. FEATURE GAP ANALYSIS (vs Agnimaster Vision)

| Agnimaster Phase | Current Status | Gap |
|------------------|----------------|-----|
| Phase 1: Business Discovery | 75% done | Missing: social profile scraping, review extraction, brand positioning analysis |
| Phase 2: Website Generation | 85% done | Missing: multi-page (pricing, blog, landing pages), multi-language |
| Phase 3: Content Engine | 60% done | Missing: blog generation, landing pages, multi-language support |
| Phase 4: Management Dashboard | 70% done | Missing: role-based access, team accounts, prompt-based updates in owner panel |
| Phase 5: Local SEO Engine | 40% done | Has keyword generation. Missing: rank tracking, auto-optimization, programmatic pages |
| Phase 6: Marketing Automation | 30% done | Has social/ad copy. Missing: campaign execution, scheduling, analytics |
| Phase 7: Voice Ecosystem | 0% | Not started. Architecture allows modular addition |
| Phase 8: Lead Generation Engine | 50% done | Has forms, WhatsApp, click-to-call. Missing: tracking, attribution, analytics |
| Phase 9: Growth Agent | 20% done | Has daily dashboard. Missing: autonomous monitoring, auto-optimization |
| Phase 10: AI Receptionist | 40% done | Chatbot exists. Missing: voice, scheduling, multi-language |

---

## 5. TECHNICAL DEBT

| Issue | Priority | Impact |
|-------|----------|--------|
| Duplicate router registrations in main.py | High | Could cause routing conflicts |
| Hardcoded localhost URLs in frontend | High | Breaks in production |
| preview.py monolithic (700 lines) | Medium | Hard to maintain/improve |
| No test suite | Medium | Risk of regressions |
| No rate limiting | Medium | Abuse risk in production |
| Redis configured but unused | Low | Missed caching opportunity |
| Unused Celery/worker infrastructure | Low | Dead code |
| No proper error recovery in agents | Medium | Silent failures |

---

## 6. REVENUE IMPACT ASSESSMENT

### Highest-Value Features to Build Next (Revenue Priority)

| Feature | Revenue Impact | Effort | Priority |
|---------|---------------|--------|----------|
| **Subscription billing (Razorpay)** | Direct revenue | Medium | 🔴 P0 |
| **Analytics dashboard (per website)** | Proves value → retention | Medium | 🔴 P0 |
| **Premium website templates** | Higher plan justification | Medium | 🟡 P1 |
| **Multi-language websites** | 10x market reach (Hindi, Marathi) | Medium | 🟡 P1 |
| **Auto blog generation** | SEO traffic → more leads | Low | 🟡 P1 |
| **Lead tracking & attribution** | Proves ROI to business owners | Medium | 🟡 P1 |
| **WhatsApp Business API** | Real automation | High | 🟢 P2 |
| **Voice narration** | Differentiator | High | 🟢 P2 |
| **Marketing campaign execution** | Full automation | High | 🟢 P2 |

---

## 7. RECOMMENDED ROADMAP

### Sprint 1 (Week 1-2): Foundation Fixes + Revenue
1. Fix duplicate router registrations in main.py
2. Fix hardcoded localhost URLs in frontend
3. Upgrade preview.py to premium design (in progress)
4. Activate Razorpay with real keys → enable subscriptions
5. Deploy stably to city-maps.online

### Sprint 2 (Week 3-4): Analytics + Retention
1. Build analytics event tracking (page views per website)
2. Build business owner dashboard showing real metrics
3. Add lead capture tracking (form submissions, calls)
4. Multi-language support (Hindi first)

### Sprint 3 (Week 5-6): SEO + Content Engine
1. Auto blog generator (weekly posts per website)
2. Programmatic landing pages for local keywords
3. SEO rank tracking (keyword positions)
4. Schema markup automation

### Sprint 4 (Week 7-8): Growth Agent
1. Autonomous monitoring of website performance
2. Auto-generate improvement recommendations
3. Campaign suggestion engine
4. Conversion funnel analysis

### Sprint 5 (Week 9-10): Voice + Advanced Marketing
1. Voice narration for websites (TTS integration)
2. WhatsApp Business API integration
3. Automated campaign execution
4. Festival/seasonal auto-campaigns

---

## 8. IMMEDIATE ACTIONS (No-Risk Improvements)

These can be done now without breaking anything:

1. ✅ Remove duplicate router registrations in main.py
2. ✅ Fix frontend hardcoded localhost URLs → use NEXT_PUBLIC_API_URL
3. ✅ Upgrade website preview design to premium
4. ✅ Add proper error handling to all routes
5. ✅ Add website slug to preview URLs for SEO-friendly links

---

*Assessment complete. Ready to proceed with Sprint 1 implementation upon approval.*
