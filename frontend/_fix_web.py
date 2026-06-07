"""Fix websites page - use api client + add error handling + loading state."""
fp = r'C:\Users\shjaisw\.kiro\Claude kiro\ai-agency-platform\frontend\src\app\websites\page.tsx'
with open(fp, 'r', encoding='utf-8') as f:
    c = f.read()

# Replace the raw fetch with the api client and add error handling
old_fetch = '''  useEffect(() => {
    fetch(`${API_BASE}/api/websites/`)
      .then((r) => r.json())
      .then(setWebsites)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);'''

new_fetch = '''  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    fetch(`${API_BASE}/api/websites/`)
      .then((r) => {
        if (!r.ok) throw new Error(`Server error: ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setWebsites(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not load websites. The server may be starting up — try refreshing in 30 seconds.");
      })
      .finally(() => setLoading(false));
  }, []);'''

if old_fetch in c:
    c = c.replace(old_fetch, new_fetch, 1)
    print("Fixed: websites fetch with error handling")
else:
    print("Fetch pattern not found - checking alternate...")
    # Maybe it already changed
    if "setError" in c:
        print("Already has error handling")
    else:
        print("WARN: Could not patch")

# Add error display in the render
old_empty = '        ) : websites.length === 0 ? (\n          <p className="text-center py-20 text-gray-400">No websites generated yet.</p>'
new_empty = '''        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-500 text-sm mb-2">{error}</p>
            <button onClick={() => window.location.reload()} className="px-4 py-2 bg-primary text-white rounded-lg text-sm">Retry</button>
          </div>
        ) : websites.length === 0 ? (
          <p className="text-center py-20 text-gray-400">No websites generated yet. Go to Leads and click "Site" to create one.</p>'''

if old_empty in c:
    c = c.replace(old_empty, new_empty, 1)
    print("Fixed: added error display + retry button")

with open(fp, 'w', encoding='utf-8') as f:
    f.write(c)
print("Done")