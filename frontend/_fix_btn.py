"""Fix the Site button to show progress while generating."""
fp = r'C:\Users\shjaisw\.kiro\Claude kiro\ai-agency-platform\frontend\src\app\leads\page.tsx'
with open(fp, 'r', encoding='utf-8') as f:
    c = f.read()

# Add a generating state
old_state = "  const [loading, setLoading] = useState(true);"
new_state = '''  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string>("");'''
c = c.replace(old_state, new_state, 1)

# Fix handleAction to show progress for generate
old_action = '''  const handleAction = async (lead: Lead, action: string) => {
    try {
      switch (action) {
        case "analyze":
          await api.leads.analyze(lead.id);
          break;
        case "generate":
          await api.websites.generate(lead.id, lead.category || "store");
          break;
        case "outreach":
          await api.outreach.send(lead.id, lead.email ? "email" : "whatsapp");
          break;
      }
      const updated = await api.leads.list(filter || undefined);
      setLeads(updated);
    } catch (err) {
      console.error(`Action ${action} failed:`, err);
    }
  };'''

new_action = '''  const handleAction = async (lead: Lead, action: string) => {
    try {
      if (action === "generate") {
        setGenerating(lead.id);
      }
      switch (action) {
        case "analyze":
          await api.leads.analyze(lead.id);
          break;
        case "generate":
          await api.websites.generate(lead.id, lead.category || "store");
          alert(`Website created for ${lead.business_name}! Check the Websites page.`);
          break;
        case "outreach":
          await api.outreach.send(lead.id, lead.email ? "email" : "whatsapp");
          break;
      }
      const updated = await api.leads.list(filter || undefined);
      setLeads(updated);
    } catch (err) {
      console.error(`Action ${action} failed:`, err);
      if (action === "generate") alert("Website generation failed. Try again.");
    } finally {
      setGenerating("");
    }
  };'''

c = c.replace(old_action, new_action, 1)

# Update the Site button to show loading state
old_btn = '''                            <button
                              onClick={() => handleAction(lead, "generate")}
                              className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                            >
                              <Globe className="w-3 h-3 inline mr-1" />
                              Site
                            </button>'''

new_btn = '''                            <button
                              onClick={() => handleAction(lead, "generate")}
                              disabled={generating === lead.id}
                              className={`text-xs px-2 py-1 rounded ${generating === lead.id ? "bg-blue-200 text-blue-400 cursor-wait" : "bg-blue-50 text-blue-600 hover:bg-blue-100"}`}
                            >
                              {generating === lead.id ? (
                                <span className="flex items-center gap-1"><span className="animate-spin inline-block w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full"></span>Building...</span>
                              ) : (
                                <><Globe className="w-3 h-3 inline mr-1" />Site</>
                              )}
                            </button>'''

c = c.replace(old_btn, new_btn, 1)

with open(fp, 'w', encoding='utf-8') as f:
    f.write(c)
print("Done - Site button now shows spinner + 'Building...' while generating")