# CITY MAPS PLATFORM - COMPLETE PROJECT SUMMARY
Last Updated: June 24, 2026

## PLATFORM OVERVIEW
- Product: City Maps - Digital Growth Platform for Local Businesses
- Website: https://city-maps.online
- Backend: https://ai-agency-platform.onrender.com (FastAPI, Python)
- Admin Frontend: https://ai-agency-platform-blush.vercel.app (Next.js)
- Business Sites: *.city-maps.online (dynamic subdomains)
- DNS: Cloudflare | Database: Supabase (PostgreSQL)
- Pricing: Rs.29/month (Growth) / Rs.39/month (Premium)
- GitHub: sjaiswal210-beep/ai-agency-platform

## QUICK ACCESS LINKS
- Admin Dashboard: https://ai-agency-platform-blush.vercel.app
- Voice Blast: https://ai-agency-platform.onrender.com/api/admin/voice-blast?pwd=kalpdev2024

## TECH STACK
Frontend: Next.js 14, Tailwind, TypeScript | Backend: FastAPI, Python 3.11
Database: Supabase | Voice: Vobiz + Sarvam AI TTS | WhatsApp: Meta Cloud API
Hosting: Render + Vercel + Contabo VPS | DNS: Cloudflare | LLM: Gemini Flash

## ENV VARS (Render)
SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY, GOOGLE_PLACES_KEY
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID
ENCRYPTION_KEY, VOBIZ_AUTH_ID, VOBIZ_AUTH_TOKEN, SARVAM_API_KEY, DEEPGRAM_API_KEY

## ENV VARS (Vercel)
NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL

## VOICE BLAST (Working)
Flow: Script > Sarvam TTS > MP3 > Vobiz Call > Play Audio > Hangup
Cost: Rs.0.50/call | Admin: /api/admin/voice-blast?pwd=kalpdev2024
Features: Script editor, speed, voice selection, language, preview


## WHATSAPP
Provider: Meta Cloud API | Phone ID: 1202589086266794
Status: Needs permanent token from Meta

## KEY FILES
backend/app/main.py, backend/app/modules/voice_calling/voice_blast.py
backend/app/api/routes/voice_blast_admin.py, frontend/src/app/page.tsx

## PENDING
1. WhatsApp permanent token 2. Razorpay payments 3. Sarvam+Vobiz audio fix

## NOTES
Admin password: kalpdev2024 | Never use "AI" in customer content