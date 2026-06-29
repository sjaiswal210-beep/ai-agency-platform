-- Fix City Maps subscription prices in LIVE voice_call_scripts to Rs.29 / Rs.39
-- Run this in Supabase SQL Editor (updates the live voice scripts)

-- Normalize plan prices (499 -> 29 Growth, 999 -> 39 Premium) across all script columns
UPDATE voice_call_scripts SET system_prompt   = REPLACE(REPLACE(system_prompt,   '499/month', '29/month'), '999/month', '39/month');
UPDATE voice_call_scripts SET whatsapp_template = REPLACE(REPLACE(whatsapp_template, '499/month', '29/month'), '999/month', '39/month');
UPDATE voice_call_scripts SET first_message    = REPLACE(REPLACE(first_message,    '499/month', '29/month'), '999/month', '39/month');

-- Optional: align plan names so Premium = top tier
UPDATE voice_call_scripts SET system_prompt = REPLACE(system_prompt, 'Business (', 'Premium-Plus (');

-- Verify
SELECT language, script_type,
       (system_prompt LIKE '%29/month%') AS has_29,
       (system_prompt LIKE '%39/month%') AS has_39
FROM voice_call_scripts;
