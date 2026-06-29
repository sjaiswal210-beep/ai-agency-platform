-- Fix City Maps subscription prices in LIVE voice_call_scripts to Rs.29 / Rs.39
-- Run this in Supabase SQL Editor (updates the live voice scripts)
-- Correct columns: agent_prompt, welcome_message, whatsapp_template

UPDATE voice_call_scripts SET agent_prompt     = REPLACE(REPLACE(agent_prompt,     '499/month', '29/month'), '999/month', '39/month');
UPDATE voice_call_scripts SET welcome_message  = REPLACE(REPLACE(welcome_message,  '499/month', '29/month'), '999/month', '39/month');
UPDATE voice_call_scripts SET whatsapp_template = REPLACE(REPLACE(whatsapp_template, '499/month', '29/month'), '999/month', '39/month');

-- Optional: align plan name so the top tier reads Premium
UPDATE voice_call_scripts SET agent_prompt = REPLACE(agent_prompt, 'Business (', 'Premium-Plus (');

-- Verify
SELECT name, language, script_type,
       (agent_prompt LIKE '%29/month%') AS has_29,
       (agent_prompt LIKE '%39/month%') AS has_39
FROM voice_call_scripts;
