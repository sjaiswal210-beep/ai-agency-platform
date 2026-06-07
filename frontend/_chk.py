fp = r'C:\Users\shjaisw\.kiro\Claude kiro\ai-agency-platform\frontend\src\app\websites\page.tsx'
with open(fp, 'r', encoding='utf-8') as f:
    c = f.read()

# Find the fetch call
import re
fetches = re.findall(r'fetch\([^)]+\)', c)
for f in fetches:
    print(repr(f))