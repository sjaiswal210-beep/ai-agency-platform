import os

src = r'C:\Users\shjaisw\.kiro\Claude kiro\ai-agency-platform\frontend\src'

for root, dirs, files in os.walk(src):
    for f in files:
        if not f.endswith('.tsx'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            c = fh.read()
        if '/api/preview/' in c:
            # These links go to backend preview - they should work via the API_BASE
            # In production, API_BASE = render backend URL, so /api/preview/{id} works
            # But the SLUG-based URLs on city-maps.online would be better
            # For now, let's just make sure they use API_BASE correctly
            print(f"{os.path.basename(fp)}: has /api/preview/ references")
            # Count occurrences
            count = c.count('/api/preview/')
            print(f"  {count} occurrences")