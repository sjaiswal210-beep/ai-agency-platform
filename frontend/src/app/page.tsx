"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

import { useEffect, useState } from "react";
import { api, DashboardStats, Lead } from "@/lib/api";
import { Users, MessageSquare, TrendingUp, Globe, Search, Mail, PlusCircle, LayoutGrid, Zap, Settings, BarChart3, Bot, ChevronLeft, Bell, StickyNote, Phone } from "lucide-react";

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentLeads, setRecentLeads] = useState<Lead[]>([]);
  const [collapsed, setCollapsed] = useState(false);
  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [showDiscover, setShowDiscover] = useState(false);
  const [location, setLocation] = useState("");
  const [keyword, setKeyword] = useState("");
  const [discovering, setDiscovering] = useState(false);
  const [discoveredCount, setDiscoveredCount] = useState<number | null>(null);
  const [country, setCountry] = useState("India");
  const [leadCount, setLeadCount] = useState(10);

  const handleDiscover = async () => {
    if (!location || !keyword) return;
    setDiscovering(true);
    setDiscoveredCount(null);
    try {
      const searchLocation = `${location}, ${country}`;
      const result = await api.leads.discover(searchLocation, keyword, leadCount);
      setDiscoveredCount(result.discovered);
      const updated = await api.dashboard.stats();
      setStats(updated);
      const leads = await api.leads.list();
      setRecentLeads(leads.slice(0, 5));
    } catch (err) {
      console.error(err);
    } finally {
      setDiscovering(false);
    }
  };

  const [showWhatsApp, setShowWhatsApp] = useState(false);
  const [showAreaScrape, setShowAreaScrape] = useState(false);
  const [showSpecificSearch, setShowSpecificSearch] = useState(false);
  const [specificName, setSpecificName] = useState("");
  const [specificPincode, setSpecificPincode] = useState("");
  const [specificSearching, setSpecificSearching] = useState(false);
  const [specificResult, setSpecificResult] = useState<any>(null);
  const [areaLocation, setAreaLocation] = useState("");
  const [areaScraping, setAreaScraping] = useState(false);
  const [areaResult, setAreaResult] = useState<number | null>(null);
  const [waLeads, setWaLeads] = useState<Lead[]>([]);
  const [waSending, setWaSending] = useState<string>("");
  const [waResult, setWaResult] = useState<{business: string; message: string; link: string} | null>(null);

  const handleSpecificSearch = async () => {
    if (!specificName) return;
    setSpecificSearching(true);
    setSpecificResult(null);
    try {
      const query = specificPincode ? `${specificName} ${specificPincode}` : specificName;
      const res = await fetch(`${API_BASE}/api/leads/search-specific?query=${encodeURIComponent(query)}`, { method: "POST" });
      const data = await res.json();
      setSpecificResult(data);
      if (data.lead) {
        const updated = await api.dashboard.stats();
        setStats(updated);
        const leads = await api.leads.list();
        setRecentLeads(leads.slice(0, 5));
      }
    } catch (err) { console.error(err); }
    finally { setSpecificSearching(false); }
  };

  const handleAreaScrape = async () => {
    if (!areaLocation) return;
    setAreaScraping(true);
    setAreaResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/leads/scrape-area?location=${encodeURIComponent(areaLocation)}`, { method: "POST" });
      const data = await res.json();
      setAreaResult(data.discovered);
      const updated = await api.dashboard.stats();
      setStats(updated);
      const leads = await api.leads.list();
      setRecentLeads(leads.slice(0, 5));
    } catch (err) { console.error(err); }
    finally { setAreaScraping(false); }
  };

  const loadWaLeads = () => {
    api.leads.list().then((leads) => {
      setWaLeads(leads.filter(l => l.phone));
      setShowWhatsApp(true);
    });
  };

  const sendWhatsApp = async (lead: Lead) => {
    setWaSending(lead.id);
    try {
      const res = await fetch(`${API_BASE}/api/whatsapp/outreach/${lead.id}`, { method: "POST" });
      const data = await res.json();
      setWaResult({ business: data.business_name, message: data.message, link: data.whatsapp_link });
    } catch (err) { console.error(err); }
    finally { setWaSending(""); }
  };

  useEffect(() => {
    api.dashboard.stats().then(setStats).catch(console.error);
    api.leads.list().then((leads) => setRecentLeads(leads.slice(0, 5))).catch(console.error);
    fetch(`${API_BASE}/api/agent-status/`).then(r => r.json()).then(setAgentStatus).catch(console.error);
  }, []);

  const navItems = [
    { name: "Dashboard", icon: LayoutGrid, href: "/", active: true },
    { name: "Leads", icon: Users, href: "/leads" },
    { name: "Websites", icon: Globe, href: "/websites" },
    { name: "Outreach", icon: Mail, href: "/outreach" },
    { name: "Editor", icon: Zap, href: "/editor" },
    { name: "Tools", icon: Bot, href: "/tools" },
    { name: "Creatives", icon: Zap, href: "/creatives" },
    { name: "Growth", icon: TrendingUp, href: "/growth" },
    { name: "Analytics", icon: BarChart3, href: "/analytics" },
    { name: "Notes", icon: StickyNote, href: "/notes" },
    { name: "Ads Manager", icon: BarChart3, href: "https://ai-agency-platform.onrender.com/api/ads/manage?pwd=kalpdev2024" },
    { name: "Growth Plan", icon: TrendingUp, href: "https://ai-agency-platform.onrender.com/api/growth-plan" },
    { name: "All Sites", icon: Globe, href: "https://ai-agency-platform.onrender.com/api/sites" },
    
    { name: "Voice Blast", icon: Phone, href: "https://ai-agency-platform.onrender.com/api/admin/voice-blast?pwd=kalpdev2024" },
    { name: "QA Agent", icon: Bot, href: "https://ai-agency-platform.onrender.com/api/qa/review-all" },
    { name: "Admin Portal", icon: Settings, href: "/admin" },
  ];

  return (
    <div className="flex min-h-screen bg-[#020817]">
      {/* Sidebar */}
      <aside className={`${collapsed ? "w-16" : "w-56"} bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col transition-all duration-200 fixed h-full z-20`}>
        <div className="p-4 flex items-center gap-2 border-b border-white/10">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Bot className="w-5 h-5 text-white" />
          </div>
          {!collapsed && <span className="font-bold text-sm text-white">City Maps</span>}
        </div>

        <nav className="flex-1 py-3 px-2 space-y-1">
          {navItems.map((item) => (
            <a key={item.name} href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                item.active ? "bg-white/10 text-white font-medium" : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}>
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </a>
          ))}
        </nav>

        <div className="border-t border-white/10 p-2">
          <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/5 hover:text-white">
            <Settings className="w-4 h-4" />
            {!collapsed && <span>Settings</span>}
          </a>
          <button onClick={() => setCollapsed(!collapsed)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/5 hover:text-white w-full">
            <ChevronLeft className={`w-4 h-4 transition ${collapsed ? "rotate-180" : ""}`} />
            {!collapsed && <span>Collapse</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className={`flex-1 ${collapsed ? "ml-16" : "ml-56"} transition-all duration-200`}>
        {/* Top bar */}
        <header className="bg-[#0f172a]/80 backdrop-blur-lg border-b border-white/5 px-6 py-3 flex items-center justify-between sticky top-0 z-10">
          <div>
            <h1 className="text-xl font-bold text-white">City-Maps Admin</h1>
            <p className="text-xs text-slate-300">Your City Maps Admin Automation Platform</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="p-2 hover:bg-white/5 rounded-lg relative">
              <Bell className="w-4 h-4 text-slate-300" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full pulse-dot"></span>
            </button>
            <div className="w-8 h-8 bg-purple-600/20 rounded-full flex items-center justify-center text-xs font-bold text-purple-400">AI</div>
          </div>
        </header>

        <div className="p-6">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 stagger-children">
            <div className="stat-card">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                <Users className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <div className="text-xl font-bold text-white">{stats?.total_leads ?? 0}</div>
                <div className="text-xs text-slate-300">Total Leads</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                <MessageSquare className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <div className="text-xl font-bold text-white">{stats?.total_outreach ?? 0}</div>
                <div className="text-xs text-slate-300">Contacted</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center flex-shrink-0">
                <TrendingUp className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <div className="text-xl font-bold text-white">{stats?.leads_by_status?.converted ?? 0}</div>
                <div className="text-xs text-slate-300">Converted</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                <Globe className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <div className="text-xl font-bold text-white">{stats?.total_websites ?? 0}</div>
                <div className="text-xs text-slate-300">Sites Generated</div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          {/* Agent Status */}
          {false && agentStatus && (
            <div className="glass-card-solid p-4 mb-6">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-3">Agents</h3>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
                {Object.entries(agentStatus.agents || {}).map(([key, agent]: [string, any]) => (
                  <div key={key} className="flex items-center gap-2 px-3 py-2 bg-slate-700/30 rounded-lg">
                    <span className="text-lg">{agent.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{agent.name}</p>
                      <p className={`text-[10px] ${agent.status === "active" ? "text-green-400" : "text-slate-300"}`}>
                        {agent.status === "active" ? "\u25cf Working" : "\u25cb Idle"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-3">Quick Actions</p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6 stagger-children">
            <button onClick={() => setShowDiscover(true)} className="flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-3 rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-indigo-500/25 transition-all">
              <PlusCircle className="w-4 h-4" /> New Campaign
            </button>
            <button onClick={() => setShowDiscover(true)} className="flex items-center justify-center gap-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-3 rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all">
              <Search className="w-4 h-4" /> Discover
            </button>
            <button onClick={() => setShowSpecificSearch(true)} className="flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-500 to-green-500 text-white py-3 rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-emerald-500/25 transition-all">
              <Search className="w-4 h-4" /> Find Business
            </button>
            <button onClick={() => setShowAreaScrape(true)} className="flex items-center justify-center gap-2 bg-gradient-to-r from-rose-500 to-pink-500 text-white py-3 rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-rose-500/25 transition-all">
              <Globe className="w-4 h-4" /> Scrape Area
            </button>
          </div>

          {/* Two column: Recent Campaigns + Recent Leads */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Pipeline */}
            <div className="glass-card-solid p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm text-white">Pipeline Status</h3>
                <a href="/leads" className="text-xs text-purple-400 hover:underline">View all &rarr;</a>
              </div>
              <div className="space-y-3">
                {Object.entries(stats?.leads_by_status || {}).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        status === "new" ? "bg-blue-400" :
                        status === "analyzed" ? "bg-purple-400" :
                        status === "outreach_sent" ? "bg-amber-400" :
                        status === "converted" ? "bg-green-400" : "bg-gray-300"
                      }`} />
                      <span className="text-sm capitalize text-white">{status.replace("_", " ")}</span>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      status === "new" ? "bg-blue-500/10 text-blue-400" :
                      status === "analyzed" ? "bg-purple-500/10 text-purple-400" :
                      status === "outreach_sent" ? "bg-amber-500/10 text-amber-400" :
                      status === "converted" ? "bg-green-500/10 text-green-400" : "bg-slate-700/30 text-slate-300"
                    }`}>{count}</span>
                  </div>
                ))}
                {Object.keys(stats?.leads_by_status || {}).length === 0 && (
                  <p className="text-xs text-slate-300 text-center py-4">No leads yet</p>
                )}
              </div>
            </div>

            {/* Recent Leads */}
            <div className="glass-card-solid p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm text-white">Recent Leads</h3>
                <a href="/leads" className="text-xs text-purple-400 hover:underline">View all &rarr;</a>
              </div>
              <div className="space-y-3">
                {recentLeads.map((lead) => (
                  <div key={lead.id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-white">{lead.business_name}</p>
                      <p className="text-xs text-slate-300">{lead.address?.split(",").slice(0, 2).join(",") || lead.category} {lead.phone ? `Ã‚Â· ${lead.phone}` : ""}</p>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      lead.status === "new" ? "bg-blue-500/10 text-blue-400" :
                      lead.status === "analyzed" ? "bg-purple-500/10 text-purple-400" :
                      lead.status === "outreach_sent" ? "bg-amber-500/10 text-amber-400" :
                      "bg-slate-700/30 text-slate-300"
                    }`}>{lead.status.replace("_", " ")}</span>
                  </div>
                ))}
                {recentLeads.length === 0 && (
                  <p className="text-xs text-slate-300 text-center py-4">No leads yet. Start discovering!</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Specific Business Search Modal */}
      {showSpecificSearch && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowSpecificSearch(false)}>
          <div className="bg-[#0f172a]/60 rounded-2xl p-6 w-full max-w-md shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-1">Find Specific Business</h2>
            <p className="text-xs text-slate-300 mb-4">Search by name + pincode. Auto-analyzes and creates website.</p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300 mb-1 block">Business Name</label>
                <input type="text" value={specificName} onChange={(e) => setSpecificName(e.target.value)}
                  placeholder="e.g., Thakurs Hair and Beauty Planet"
                  className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300 mb-1 block">Pincode / Area (optional)</label>
                <input type="text" value={specificPincode} onChange={(e) => setSpecificPincode(e.target.value)}
                  placeholder="e.g., 411014 or Wagholi Pune"
                  className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  onKeyDown={(e) => e.key === "Enter" && handleSpecificSearch()} />
              </div>

              {specificResult && (
                <div className={`rounded-lg p-3 ${specificResult.lead ? "bg-green-500/10 border border-green-200" : "bg-red-50 border border-red-200"}`}>
                  {specificResult.lead ? (
                    <div>
                      <p className="text-sm text-green-400 font-medium">{specificResult.lead.business_name}</p>
                      <p className="text-xs text-green-600 mt-1">{specificResult.lead.phone} | {specificResult.lead.address?.split(",").slice(0,2).join(",")}</p>
                      {specificResult.website_id && (
                        <a href={specificResult.slug ? `https://${specificResult.slug}.city-maps.online` : `${API_BASE}/api/preview/${specificResult.website_id}`} target="_blank" rel="noopener noreferrer"
                          className="inline-block mt-2 text-xs bg-green-600 text-white px-3 py-1 rounded-lg">{specificResult.slug ? `Live: ${specificResult.slug}.city-maps.online` : "View Website"}</a>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-red-600">{specificResult.error || "Business not found"}</p>
                  )}
                </div>
              )}

              <button onClick={handleSpecificSearch} disabled={specificSearching || !specificName}
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-500 to-green-500 text-white py-3 rounded-xl text-sm font-medium disabled:opacity-50 hover:shadow-lg transition-all">
                {specificSearching ? "Searching & building..." : "Find & Create Website"}
              </button>
            </div>

            <button onClick={() => setShowSpecificSearch(false)} className="mt-3 w-full text-center text-xs text-slate-300 hover:text-slate-300">Close</button>
          </div>
        </div>
      )}

      {/* Area Scrape Modal */}
      {showAreaScrape && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowAreaScrape(false)}>
          <div className="bg-[#0f172a]/60 rounded-2xl p-6 w-full max-w-md shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-1">Scrape All Businesses in Area</h2>
            <p className="text-xs text-slate-300 mb-4">Find ALL businesses in a location. AI will auto-tag categories.</p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300 mb-1 block">Location / Area</label>
                <input type="text" value={areaLocation} onChange={(e) => setAreaLocation(e.target.value)}
                  placeholder="e.g., Kharadi Pune, MG Road Bangalore, Connaught Place Delhi"
                  className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  onKeyDown={(e) => e.key === "Enter" && handleAreaScrape()} />
              </div>

              <p className="text-xs text-slate-300">This will search for all types of businesses (shops, restaurants, clinics, salons, etc.) in the area and AI will categorize them automatically.</p>

              {areaResult !== null && (
                <div className="bg-green-500/10 border border-green-200 rounded-lg p-3">
                  <p className="text-sm text-green-400 font-medium">Found & categorized {areaResult} businesses!</p>
                </div>
              )}

              <button onClick={handleAreaScrape} disabled={areaScraping || !areaLocation}
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-rose-500 to-pink-500 text-white py-3 rounded-xl text-sm font-medium disabled:opacity-50 hover:shadow-lg transition-all">
                {areaScraping ? "Scraping & categorizing..." : "Scrape All Businesses"}
              </button>
            </div>

            <button onClick={() => setShowAreaScrape(false)} className="mt-3 w-full text-center text-xs text-slate-300 hover:text-slate-300">Close</button>
          </div>
        </div>
      )}

      {/* WhatsApp Outreach Modal */}
      {showWhatsApp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => { setShowWhatsApp(false); setWaResult(null); }}>
          <div className="bg-[#0f172a]/60 rounded-2xl p-6 w-full max-w-lg shadow-xl max-h-[85vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-white">WhatsApp Outreach</h2>
                <p className="text-xs text-slate-300">{waLeads.length} leads with phone numbers</p>
              </div>
              <button onClick={() => { setShowWhatsApp(false); setWaResult(null); }} className="text-slate-300 hover:text-slate-300 text-xl">&times;</button>
            </div>

            {waResult ? (
              <div className="flex-1 overflow-y-auto">
                <p className="text-sm font-medium mb-2">Message for {waResult.business}:</p>
                <div className="bg-slate-700/30 rounded-lg p-3 text-sm whitespace-pre-wrap mb-4 border max-h-48 overflow-y-auto">{waResult.message}</div>
                <div className="flex gap-2">
                  <a href={waResult.link} target="_blank" rel="noopener noreferrer"
                    className="flex-1 flex items-center justify-center gap-2 bg-green-500/100 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-green-600">
                    Open WhatsApp & Send
                  </a>
                  <button onClick={() => { navigator.clipboard.writeText(waResult.message); }}
                    className="px-4 py-2.5 bg-white/5 rounded-xl text-sm hover:bg-white/10">Copy</button>
                </div>
                <button onClick={() => setWaResult(null)} className="mt-3 w-full text-xs text-purple-400 hover:underline">Back to list</button>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto space-y-2">
                {waLeads.map((lead) => (
                  <div key={lead.id} className="flex items-center justify-between p-3 border border-white/5 rounded-lg hover:bg-[#020817]">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{lead.business_name}</p>
                      <p className="text-xs text-slate-300">{lead.phone} &middot; {lead.category}</p>
                    </div>
                    <button onClick={() => sendWhatsApp(lead)} disabled={waSending === lead.id}
                      className="ml-2 px-3 py-1.5 bg-green-500/100 text-white text-xs rounded-lg hover:bg-green-600 disabled:opacity-50 flex-shrink-0">
                      {waSending === lead.id ? "..." : "Send"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Discovery Modal */}
      {showDiscover && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowDiscover(false)}>
          <div className="bg-[#0f172a]/60 rounded-2xl p-6 w-full max-w-lg shadow-xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-1">Discover New Leads</h2>
            <p className="text-xs text-slate-300 mb-4">Search Google Maps for real businesses with phone numbers</p>

            <div className="space-y-4">
              {/* Country */}
              <div>
                <label className="text-xs font-medium text-slate-300 mb-1 block">Country</label>
                <select value={country} onChange={(e) => setCountry(e.target.value)}
                  className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50">
                  <option value="India">India</option>
                  <option value="USA">USA</option>
                  <option value="UK">UK</option>
                  <option value="UAE">UAE</option>
                  <option value="Australia">Australia</option>
                  <option value="Canada">Canada</option>
                  <option value="Singapore">Singapore</option>
                  <option value="Germany">Germany</option>
                </select>
              </div>

              {/* Location */}
              <div>
                <label className="text-xs font-medium text-slate-300 mb-1 block">City / Area</label>
                <input type="text" value={location} onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g., Pune, Mumbai, Kharadi, Baner"
                  className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" />
              </div>

              {/* Category - preset + custom */}
              <div>
                <label className="text-xs font-medium text-slate-300 mb-1 block">Category</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {["restaurant", "gym", "salon", "dentist", "clinic", "hotel", "cafe", "plumber", "lawyer", "photographer", "school", "solar", "real estate", "spa"].map((cat) => (
                    <button key={cat} onClick={() => setKeyword(cat)}
                      className={`px-3 py-1 rounded-full text-xs font-medium border transition ${
                        keyword === cat ? "bg-purple-600 text-white border-primary" : "bg-slate-700/30 text-slate-300 border-white/10 hover:border-primary hover:text-purple-400"
                      }`}>{cat}</button>
                  ))}
                </div>
                <input type="text" value={keyword} onChange={(e) => setKeyword(e.target.value)}
                  placeholder="Or type any keyword: electrician, tailor, pet shop..."
                  className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50" />
              </div>

              {/* Count */}
              <div>
                <label className="text-xs font-medium text-slate-300 mb-1 block">Number of Leads</label>
                <div className="flex gap-2">
                  {[5, 10, 15, 20].map((n) => (
                    <button key={n} onClick={() => setLeadCount(n)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium border transition ${
                        leadCount === n ? "bg-purple-600 text-white border-primary" : "bg-slate-700/30 text-slate-300 border-white/10 hover:border-primary"
                      }`}>{n}</button>
                  ))}
                </div>
              </div>

              {discoveredCount !== null && (
                <div className="bg-green-500/10 border border-green-200 rounded-lg p-3">
                  <p className="text-sm text-green-400 font-medium">Found {discoveredCount} businesses with phone numbers!</p>
                </div>
              )}

              <button onClick={handleDiscover} disabled={discovering || !location || !keyword}
                className="w-full flex items-center justify-center gap-2 bg-purple-600 text-white py-3 rounded-xl text-sm font-medium disabled:opacity-50 hover:bg-purple-600-dark transition">
                {discovering ? "Searching Google Maps..." : <><Search className="w-4 h-4" /> Search & Add Leads</>}
              </button>
            </div>

            <button onClick={() => setShowDiscover(false)} className="mt-3 w-full text-center text-xs text-slate-300 hover:text-slate-300">
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

