# City Maps - Pre-Launch Audit, Legal Pack & Growth Plan
Prepared overnight for review. Nothing here was deployed without your approval where noted.

==================================================================
## PART A - LEGAL & COMPLIANCE AUDIT (India)
==================================================================

You are registering a company and taking online payments (Razorpay).
Razorpay + Indian law (IT Act, DPDP Act 2023, Consumer Protection 2019,
GST, TRAI for calls/WhatsApp) require the items below.

### A1. CRITICAL GAPS (must fix before launch)

1. NO Refund & Cancellation Policy page
   - Razorpay MANDATES this before activating live payments.
   - Draft provided in PART C below.

2. NO Shipping/Service Delivery Policy
   - Razorpay requires it even for digital services ('how/when service is delivered').
   - Draft provided in PART C.

3. Privacy Policy is too thin for DPDP Act 2023
   - Missing: legal basis/consent, data retention, user rights, grievance officer
     name+email, children's data, cross-border transfer, security measures.
   - Razorpay also checks this. Full rewrite in PART C.

4. Terms of Service is too thin
   - Missing: pricing/billing terms, auto-renewal, account suspension, IP,
     governing law/jurisdiction, dispute resolution, company legal name.
   - Full rewrite in PART C.

5. NO company identity on site
   - Razorpay + law require: registered business name, full address, GSTIN
     (once registered), contact email + phone on Contact page and footer.
   - Currently only 'Powered by Kalpdev Digitals | WhatsApp +91 7350785606'.

6. NO clear consent for WhatsApp/voice marketing (TRAI / DPDP)
   - You auto-send WhatsApp + place voice calls. Need explicit consent capture
     + opt-out. Add a consent checkbox on the phone-capture gate and an
     unsubscribe/STOP path. TRAI TCCCPR governs commercial calls/SMS.

7. Pricing transparency
   - Razorpay requires clear pricing visible to buyers. You have Rs.29/Rs.39
     on the landing + panel - GOOD. Ensure GST inclusive/exclusive is stated.

### A2. MEDIUM PRIORITY
- Cookie/analytics notice (you use Google/Meta analytics).
- 'Ads on generated websites' clause: Terms say ad revenue belongs to you -
  make sure customers consent to ads on their site at signup (it's in Terms,
  but surface it at the create-site step).
- Data deletion endpoint (/api/data-deletion) referenced in Privacy - confirm
  it actually works end to end.
- Email: support@city-maps.online referenced - ensure the inbox exists.

### A3. TECHNICAL / SECURITY NOTES FOUND
- Admin tools are protected only by pwd=kalpdev2024 in the URL
  (/api/whatsapp/test-send, /diag, /register, /admin/*, voice-blast, etc.).
  RISK: anyone with the URL can send WhatsApp/calls, view visitor phone data,
  or change credits. RECOMMEND before launch:
    * Move admin auth to a server-side session/token, not a URL password.
    * At minimum, rotate the password and remove /diag and /register after setup.
- owner_credits can be set via SQL only; no audit trail on credit changes.
- OTP store is in-memory (resets on redeploy) - fine for now, use Redis later.
- No rate limiting on /api/dashboard-access/track or OTP send (spam risk).
- Secrets: ensure .env is never committed (it is gitignored - verify).

==================================================================
## PART B - REVENUE & GROWTH FEATURES (ideas to earn more)
==================================================================

### B1. Already monetized
- Subscription: Rs.29 Growth / Rs.39 Premium per month
- AI Logo: Rs.5 each (credits)
- AI Video: Rs.5 each (credits)
- Voice Broadcast: 5 free lifetime, then Rs.1/call (credits)

### B2. HIGH-IMPACT additions (recommended, ranked)
1. Razorpay 'Buy Credits' wallet (BLOCKER for all paid tools)
   - Owners top up Rs.50/100/500; credits used for logo/video/calls.
   - Without this, paid tools cannot actually earn. Build this FIRST.
2. Annual plans (Rs.290/yr Growth, Rs.390/yr Premium = 2 months free)
   - Improves cash flow + retention; standard SaaS lever.
3. Add-on marketplace (per-use, from credits):
   - WhatsApp bulk campaign (Rs.0.50/msg), Festival poster pack (Rs.10),
     Google review-request blast, AI product description writer (Rs.2).
4. Domain sales: custom domain for the business site (Rs.299/yr, you markup).
5. 'Verified/Featured' listing on city-maps.online city pages (Rs.99/mo).
6. Lead-gen upsell: paid ad campaigns managed for the owner (% or flat).
7. Reseller / agency tier: let other agencies white-label and resell
   (recurring B2B revenue) - see PART D.
8. Payment links / online store checkout for the business (small txn fee).

### B3. RETENTION / STICKINESS
- Monthly auto-report on WhatsApp (visits, calls, leads) - keeps value visible.
- Streaks/gamified 'business health score' (you already have health_score).
- Referral program: owner refers another business -> both get credits.

==================================================================
## PART D - WHITE-LABEL PLAN
==================================================================

Goal: every surface is brandable so you (or resellers) can rebrand.

### What to make configurable (per-organization or per-reseller):
- Brand name, logo, primary color (you already store brand_color/logo_url).
- Domain: reseller uses their own domain pointing to the platform.
- 'Powered by' footer toggle (hide City Maps branding for white-label tier).
- Email sender name + WhatsApp sender (per reseller WABA).
- Pricing: reseller sets their own plan prices + keeps margin.

### Suggested build order:
1. Add a 'brands' table: id, name, logo, color, domain, support_email,
   wa_phone_id, hide_powered_by, owner_account_id.
2. Resolve brand by request host (domain) -> theme the panel + emails + sites.
3. Reseller dashboard: manage their businesses, see their revenue.
4. Billing: platform charges reseller (B2B), reseller charges end business.

==================================================================
## PART E - PRE-LAUNCH CHECKLIST
==================================================================

LEGAL (see PART C drafts):
- [ ] Publish Terms, Privacy (DPDP), Refund, Shipping/Delivery, Contact pages
- [ ] Add company legal name + address + GSTIN + email + phone to footer
- [ ] Add consent checkbox on phone-capture + WhatsApp/calls opt-out
- [ ] Name a Grievance Officer (DPDP) with email on Privacy page
- [ ] State GST treatment on pricing (inclusive/exclusive)

PAYMENTS:
- [ ] Complete Razorpay KYC with the registered company
- [ ] Build 'Buy Credits' + subscription checkout (Razorpay)
- [ ] Test a live Rs.1 transaction end to end

SECURITY:
- [ ] Replace URL-password admin auth with proper session/token
- [ ] Remove /api/whatsapp/diag and /register after setup; rotate password
- [ ] Add rate limiting to OTP + track endpoints
- [ ] Confirm .env is gitignored and no secrets in repo

GO-LIVE SWITCHES (currently in testing):
- [ ] LEAD_NOTIFY_OVERRIDE = '' (send to real owners)
- [ ] CALL_NOTIFY_OVERRIDE = '' (call real owners)
- [ ] follow-up call delay back to 10 min
- [ ] site_ready WhatsApp template APPROVED
- [ ] run scripts/fix_voice_prices.sql in Supabase
