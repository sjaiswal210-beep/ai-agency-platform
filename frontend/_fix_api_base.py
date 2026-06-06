import os

src = r'C:\Users\shjaisw\.kiro\Claude kiro\ai-agency-platform\frontend\src'
fixed = 0

for root, dirs, files in os.walk(src):
    for f in files:
        if not f.endswith('.tsx'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            c = fh.read()
        
        if '${API_BASE}' in c:
            # Fix the broken fallback
            c = c.replace(
                'process.env.NEXT_PUBLIC_API_URL || "${API_BASE}"',
                'process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"'
            )
            # Also fix any remaining ${API_BASE} in fetch calls that should use the variable
            # These should be backtick template literals using the const
            with open(fp, 'w', encoding='utf-8') as fh:
                fh.write(c)
            fixed += 1
            print(f"Fixed: {os.path.basename(fp)}")

print(f"\nTotal fixed: {fixed}")