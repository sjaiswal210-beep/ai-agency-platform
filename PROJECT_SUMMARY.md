# CITY MAPS PLATFORM - PROJECT SUMMARY
Last Updated: June 22, 2026

## PLATFORM OVERVIEW
- Product: City Maps - Digital Growth Platform for Local Businesses
- Website: https://city-maps.online
- Backend: https://ai-agency-platform.onrender.com (FastAPI, Docker)
- Admin: https://ai-agency-platform-blush.vercel.app (Next.js)
- Business Sites: *.city-maps.online (dynamic subdomains)
- FreeLLMAPI: https://freellmapi-rn6c.onrender.com
- DNS: Cloudflare | Database: Supabase
- Pricing: Rs.29/month (Growth) / Rs.39/month (Premium)

## DEMO SITE
- Website: https://spice-garden.city-maps.online
- Dashboard: https://ai-agency-platform.onrender.com/api/panel/27b0a862-60c5-406e-a32a-47dde32823bb
- Store: https://ai-agency-platform.onrender.com/api/store/27b0a862-60c5-406e-a32a-47dde32823bb/store-page

## PENDING ITEMS
1. WhatsApp permanent token (HIGH - need from Meta)
2. Razorpay payment integration (HIGH - Rs.29/39 plans)
3. Google scope verification (WAITING 2-4 weeks)
4. WhatsApp bot + auto-send (blocked by #1)
5. Admin analytics password (LOW)
6. Bookings time settings (MEDIUM)
7. Render upgrade recommended (Rs.600/mo)

## ENV VARS (Render)
SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY, REPLICATE_TOKEN, HF_TOKEN, FREELLMAPI_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_PLACES_KEY, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, ENCRYPTION_KEY, NODE_ENV

## KEY FILES
- backend/app/main.py (Homepage, middleware)
- backend/app/api/routes/preview.py (Business websites)
- backend/app/api/routes/owner_panel.py (Dashboard + tools)
- backend/app/api/routes/ecommerce.py (Store)
- backend/app/api/routes/video.py (Video gen)
- backend/app/core/llm.py (LLM chain)
- backend/app/agents/website_generation/agent.py (Website creation)

## IMPORTANT NOTES
- Never use "AI" in customer-facing content - use "Auto"
- Ad Manager password: kalpdev2024
- WhatsApp Phone ID: 1202589086266794
- Google verification: 39nzaqNCoWxNXFyhZTNOUSSWZiHY9rCEpDFzvEakUo4
- Cloudflare timeout: 100s - AI features call Render directly
- All tools open in new tabs (not modals)

## PROFIT MODEL
- 50 businesses: Rs.1,450 revenue / Rs.67 cost = Rs.1,383 profit
- 500 businesses: Rs.14,500 / Rs.2,700 = Rs.11,800 profit
- 10,000 businesses: Rs.2,90,000 / Rs.17,000 = Rs.2,73,000 profit (94% margin)
