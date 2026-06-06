"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "${API_BASE}";
import { useEffect, useState } from "react";
import { api, Lead } from "@/lib/api";
import { Bot, ArrowLeft, Search, TrendingUp, Mail, Calendar, Target, Star, BarChart3, Copy, Check } from "lucide-react";

const TOOLS = [
  { id: "seo-keywords", name: "SEO Keywords", icon: "🔍", desc: "Google ranking keywords strategy", endpoint: "seo-keywords" },
  { id: "google-ads", name: "Google Ads Copy", icon: "📢", desc: "Ready-to-use ad campaigns", endpoint: "google-ads" },
  { id: "social-calendar", name: "Social Media Calendar", icon: "📅", desc: "7-day content plan", endpoint: "social-calendar" },
  { id: "competitor-analysis", name: "Competitor Analysis", icon: "🎯", desc: "Market position & strategy", endpoint: "competitor-analysis" },
  { id: "email-sequence", name: "Email Marketing", icon: "✉️", desc: "5-email retention sequence", endpoint: "email-sequence" },
  { id: "growth-plan", name: "90-Day Growth Plan", icon: "🚀", desc: "Week-by-week action plan", endpoint: "growth-plan" },
  { id: "review-strategy", name: "Review Strategy", icon: "⭐", desc: "Get 100+ Google reviews", endpoint: "review-strategy" },
];

export default function GrowthPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState("");
  const [activeTool, setActiveTool] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.leads.list().then(setLeads).catch(console.error);
  }, []);

  const runTool = async (toolEndpoint: string) => {
    if (!selectedLead) return;
    setLoading(true);
    setResult("");
    setActiveTool(toolEndpoint);
    try {
      const res = await fetch(`${API_BASE}/api/growth/${selectedLead}/${toolEndpoint}`, { method: "POST" });
      const data = await res.json();
      setResult(data.keywords || data.ads || data.calendar || data.analysis || data.emails || data.plan || data.strategy || JSON.stringify(data, null, 2));
    } catch { setResult("Error: Could not generate"); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 px-6 py-3 sticky top-0 z-10">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <Bot className="w-7 h-7 text-primary" />
            <h1 className="text-lg font-bold">Growth Tools</h1>
          </div>
          <select value={selectedLead} onChange={(e) => setSelectedLead(e.target.value)}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white max-w-xs">
            <option value="">Select a business...</option>
            {leads.map((l) => (
              <option key={l.id} value={l.id}>{l.business_name} ({l.category})</option>
            ))}
          </select>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {!selectedLead ? (
          <div className="text-center py-20 text-gray-400">
            <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Select a business above to access growth tools</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ minHeight: "calc(100vh - 120px)" }}>
            {/* Tools list */}
            <div className="space-y-2">
              {TOOLS.map((tool) => (
                <button key={tool.id} onClick={() => runTool(tool.endpoint)} disabled={loading}
                  className={`w-full text-left p-4 rounded-xl border transition hover-lift ${
                    activeTool === tool.endpoint ? "bg-primary/5 border-primary/30" : "bg-white border-gray-100 hover:border-gray-200"
                  }`}>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{tool.icon}</span>
                    <div>
                      <p className="text-sm font-semibold">{tool.name}</p>
                      <p className="text-xs text-gray-500">{tool.desc}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Result */}
            <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 overflow-hidden flex flex-col">
              <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                <h3 className="font-semibold text-sm">{loading ? "Generating..." : activeTool ? "Result" : "Select a tool"}</h3>
                {result && (
                  <button onClick={() => { navigator.clipboard.writeText(result); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
                    className="flex items-center gap-1 px-3 py-1 text-xs bg-gray-100 rounded-lg hover:bg-gray-200">
                    {copied ? <><Check className="w-3 h-3 text-green-500" /> Copied</> : <><Copy className="w-3 h-3" /> Copy All</>}
                  </button>
                )}
              </div>
              <div className="flex-1 p-4 overflow-y-auto">
                {loading && <div className="flex items-center justify-center h-full"><div className="text-center"><div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-3"></div><p className="text-sm text-gray-500">Generating strategy...</p></div></div>}
                {!loading && !result && <div className="flex items-center justify-center h-full text-gray-400 text-sm">Click a tool to generate growth strategy</div>}
                {!loading && result && <pre className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed font-sans">{result}</pre>}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
