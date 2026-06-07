fp = r'C:\Users\shjaisw\.kiro\Claude kiro\ai-agency-platform\frontend\src\app\websites\page.tsx'
with open(fp, 'r', encoding='utf-8') as f:
    c = f.read()
# Show first 10 lines
lines = c.split('\n')
for i in range(min(10, len(lines))):
    print(f"{i+1}: {lines[i]}")