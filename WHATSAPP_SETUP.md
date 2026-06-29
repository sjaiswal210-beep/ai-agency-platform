# WhatsApp Cloud API - Activation Guide
For City Maps mobile app OTP + business messaging

This sets up Meta WhatsApp Cloud API (free tier: 1000 conversations/month).

---

## WHAT YOU NEED BEFORE STARTING

- A Facebook account
- A business phone number that is NOT already on WhatsApp
  (or delete the existing WhatsApp account on that number first)
- 15-20 minutes

---

## STEP 1: Create Meta Business Account

1. Go to https://business.facebook.com
2. Click 'Create Account'
3. Enter business name (City Maps), your name, email
4. Confirm email

---

## STEP 2: Create a Developer App

1. Go to https://developers.facebook.com/apps
2. Click 'Create App'
3. Choose use case: 'Other' -> Type: 'Business'
4. App name: City Maps  |  Link to your Business Account
5. Create app

---

## STEP 3: Add WhatsApp Product

1. In the app dashboard, find 'WhatsApp' -> click 'Set up'
2. It auto-creates a WhatsApp Business Account (WABA)
3. You get a FREE test number to start

On the WhatsApp -> API Setup page you will see:
- Temporary access token (valid 24 hours) <- for testing only
- Phone number ID <- this is WHATSAPP_PHONE_ID
- WhatsApp Business Account ID (WABA ID)

---

## STEP 4: Test It Works (with temp token)

On the API Setup page, add YOUR personal number as a recipient,
then click 'Send message'. If you receive the test 'hello_world'
message on WhatsApp, the connection works.

---

## STEP 5: Get a PERMANENT Token (System User)

The temp token expires in 24h. For production you need a permanent one.

1. Go to https://business.facebook.com/settings
2. Left menu -> Users -> System Users
3. Click 'Add' -> name it 'citymaps-api' -> role: Admin
4. Click the system user -> 'Add Assets' -> select your App -> full control
5. Click 'Generate New Token'
   - Select your app
   - Token expiration: Never
   - Permissions: check whatsapp_business_messaging AND
     whatsapp_business_management
6. Copy the token NOW (shown only once) <- this is WHATSAPP_TOKEN

---

## STEP 6: Create the OTP Template

1. Go to https://business.facebook.com/wa/manage/message-templates
   (or WhatsApp Manager -> Message Templates)
2. Click 'Create Template'
3. Category: AUTHENTICATION
4. Name: login_otp   (lowercase, must match exactly)
5. Language: English
6. Use the default authentication layout:
   - Body: auto-generated ({{1}} is your verification code)
   - Include the 'Copy code' button (default)
7. Submit. Approval is usually within minutes for auth templates.

If you name it differently, set WHATSAPP_OTP_TEMPLATE on Render to match.

---

## STEP 7: Add Credentials to Render (Backend)

1. Go to https://dashboard.render.com
2. Open your ai-agency-platform service -> Environment
3. Add / update these:

   WHATSAPP_TOKEN = <permanent token from Step 5>
   WHATSAPP_PHONE_ID = <phone number ID from Step 3>
   WHATSAPP_OTP_TEMPLATE = login_otp
   WHATSAPP_OTP_LANG = en

4. Save -> Render auto-redeploys

---

## STEP 8: Test OTP From The App

1. Open the mobile app -> enter a registered business phone
2. You should receive the OTP on WhatsApp
3. Enter it -> dashboard opens

---

## IMPORTANT NOTES

- FREE TEST NUMBER: can only message numbers you manually add as
  recipients (max 5). Good for testing, not for real customers.
- REAL CUSTOMERS: you must add and verify YOUR OWN business number
  (WhatsApp Manager -> Phone Numbers -> Add). Requires business
  verification for higher limits.
- BUSINESS VERIFICATION: needed to message unlimited numbers and
  raise the daily limit. Do this in Business Settings -> Security Center.
- AUTH templates are required for OTP to people who have NOT messaged
  you in the last 24h. The code already uses this template format.

---

## WHAT THE CODE ALREADY DOES

- backend/app/services/whatsapp_auto.py -> send_whatsapp_otp()
  sends via the login_otp template, falls back to plain text / dev mode
- backend/app/api/routes/mobile_auth.py -> /send-otp and /verify-otp
- Until WHATSAPP_TOKEN is set, OTP is returned in the API response
  (dev mode) so you can keep testing.
