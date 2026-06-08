"""Fix ALL frontend pages to use a runtime-safe API URL detection."""
import os, re

src = r'C:\Users\shjaisw\.kiro\Claude kiro\ai-agency-platform\frontend\src'

# The fix: instead of relying solely on NEXT_PUBLIC_API_URL (build-time),
# add a runtime check that detects production
old_pattern = 'const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";'
new_pattern = 'const API_BASE = process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://ai-agency-platform.onrender.com" : "http://localhost:8000");'

fixed = 0
for root, dirs, files in os.walk(src):
    for f in files:
        if not f.endswith('.tsx'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            c = fh.read()
        if old_pattern in c:
            c = c.replace(old_pattern, new_pattern)
            with open(fp, 'w', encoding='utf-8') as fh:
                fh.write(c)
            fixed += 1
            print(f"Fixed: {f}")

# Also fix api.ts
api_fp = os.path.join(src, 'lib', 'api.ts')
with open(api_fp, 'r', encoding='utf-8') as f:
    c = f.read()

old_api = 'const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";'
new_api = 'const API_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://ai-agency-platform.onrender.com" : "http://localhost:8000");'

if old_api in c:
    c = c.replace(old_api, new_api)
    with open(api_fp, 'w', encoding='utf-8') as f:
        f.write(c)
    fixed += 1
    print("Fixed: api.ts")

print(f"\nTotal: {fixed} files fixed")