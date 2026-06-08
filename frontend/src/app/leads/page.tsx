"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://ai-agency-platform.onrender.com" : "http://localhost:8000");

import { useEffect, useState } from "react";
import { api, Lead } from "@/lib/api";
import { Bot, Globe, Mail, Star, ArrowLeft, Phone } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-100 text-blue-700",
  analyzed: "bg-purple-100 text-purple-700",
  outreach_sent: "bg-amber-100 text-amber-700",
  responded: "bg-emerald-100 text-emerald-700",
  interested: "bg-green-100 text-green-700",
  converted: "bg-green-200 text-green-800",
  lost: "bg-gray-100 text-gray-500",
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string>("");
  

  useEffect(() => {
    setLoading(true);
    api.leads
      .list(filter || undefined)
      .then(setLeads)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filter]);

  const [waMessage, setWaMessage] = useState<{link: string; message: string; business: string} | null>(null);

  const handleWhatsApp = async (lead: Lead) => {
    try {
      const res = await fetch(`${API_BASE}/api/whatsapp/outreach/${lead.id}`, { method: "POST" });
      const data = await res.json();
      setWaMessage({ link: data.whatsapp_link, message: data.message, business: data.business_name });
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (lead: Lead) => {
    if (!confirm(`Delete ${lead.business_name}? This also removes its website.`)) return;
    try {
      await fetch(`${API_BASE}/api/leads/${lead.id}`, { method: "DELETE" });
      setLeads(leads.filter(l => l.id !== lead.id));
    } catch (err) { console.error(err); }
  };

  const handleAction = async (lead: Lead, action: string) => {
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
  };

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-gray-600">
              <ArrowLeft className="w-5 h-5" />
            </a>
            <Bot className="w-8 h-8 text-primary" />
            <h1 className="text-xl font-bold">Leads</h1>
            <span className="text-sm text-gray-400">({leads.length})</span>
          </div>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm"
          >
            <option value="">All Statuses</option>
            <option value="new">New</option>
            <option value="analyzed">Analyzed</option>
            <option value="outreach_sent">Outreach Sent</option>
            <option value="responded">Responded</option>
            <option value="interested">Interested</option>
            <option value="converted">Converted</option>
            <option value="lost">Lost</option>
          </select>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Business</th>
                  <th className="text-left px-4 py-3 font-medium">Phone</th>
                  <th className="text-left px-4 py-3 font-medium">Category</th>
                  <th className="text-left px-4 py-3 font-medium">Rating</th>
                  <th className="text-left px-4 py-3 font-medium">Score</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                  <th className="text-left px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr key={lead.id} className={`border-b last:border-0 hover:bg-gray-50 border-l-4 ${
                        lead.status === "new" ? "border-l-blue-400" :
                        lead.status === "analyzed" ? "border-l-purple-400" :
                        lead.status === "outreach_sent" ? "border-l-amber-400" :
                        lead.status === "converted" ? "border-l-green-400" : "border-l-gray-200"
                      }`}>
                    <td className="px-4 py-3">
                      <p className="font-medium text-sm">{lead.business_name}</p>
                      <p className="text-xs text-gray-500 truncate max-w-[250px]">{lead.address}</p>
                    </td>
                    <td className="px-4 py-3">
                      {lead.phone ? (
                        <a href={`tel:${lead.phone}`} className="flex items-center gap-1 text-blue-600 hover:underline text-sm">
                          <Phone className="w-3 h-3" />
                          {lead.phone}
                        </a>
                      ) : (
                        <span className="text-gray-400 text-xs">No phone</span>
                      )}
                    </td>
                    <td className="px-4 py-3 capitalize text-sm">{lead.category}</td>
                    <td className="px-4 py-3">
                      {lead.rating && (
                        <span className="flex items-center gap-1 text-sm">
                          <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                          {lead.rating}
                          {lead.review_count ? <span className="text-gray-400 text-xs">({lead.review_count})</span> : null}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {lead.opportunity_score != null && (
                        <span className="font-mono text-sm">{lead.opportunity_score.toFixed(0)}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_COLORS[lead.status] || "bg-gray-100"}`}>
                        {lead.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {lead.status === "new" && (
                          <button
                            onClick={() => handleAction(lead, "analyze")}
                            className="text-xs px-2 py-1 bg-purple-50 text-purple-600 rounded hover:bg-purple-100"
                          >
                            Analyze
                          </button>
                        )}
                        {(lead.status === "new" || lead.status === "analyzed" || lead.status === "outreach_sent") && (
                          <>
                            <button
                              onClick={() => handleWhatsApp(lead)}
                              className="text-xs px-2 py-1 bg-green-50 text-green-600 rounded hover:bg-green-100"
                              title="Send WhatsApp"
                            >
                              WhatsApp
                            </button>
                            <button
                              onClick={() => handleAction(lead, "generate")}
                              disabled={generating === lead.id}
                              className={`text-xs px-2 py-1 rounded ${generating === lead.id ? "bg-blue-200 text-blue-400 cursor-wait" : "bg-blue-50 text-blue-600 hover:bg-blue-100"}`}
                            >
                              {generating === lead.id ? (
                                <span className="flex items-center gap-1"><span className="animate-spin inline-block w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full"></span>Building...</span>
                              ) : (
                                <><Globe className="w-3 h-3 inline mr-1" />Site</>
                              )}
                            </button>
                            <button
                              onClick={() => handleAction(lead, "outreach")}
                              className="text-xs px-2 py-1 bg-green-50 text-green-600 rounded hover:bg-green-100"
                            >
                              <Mail className="w-3 h-3 inline mr-1" />
                              Reach
                            </button>
                          </>
                        )}
                        <button
                              onClick={() => handleDelete(lead)}
                              className="text-xs px-2 py-1 bg-red-50 text-red-600 rounded hover:bg-red-100"
                            >
                              Del
                            </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {loading && <p className="text-center py-12 text-gray-400">Loading leads...</p>}
          {!loading && leads.length === 0 && (
            <p className="text-center py-12 text-gray-400">
              No leads found. Start by discovering leads from the dashboard.
            </p>
          )}
        </div>
      </main>

      {/* WhatsApp Message Modal */}
      {waMessage && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setWaMessage(null)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-bold mb-1">WhatsApp Outreach</h3>
            <p className="text-xs text-gray-500 mb-3">Message for {waMessage.business}</p>
            <div className="bg-gray-50 rounded-lg p-3 text-sm whitespace-pre-wrap mb-4 max-h-60 overflow-y-auto border">
              {waMessage.message}
            </div>
            <div className="flex gap-2">
              <a href={waMessage.link} target="_blank" rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-2 bg-green-500 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-green-600">
                Open WhatsApp
              </a>
              <button onClick={() => {navigator.clipboard.writeText(waMessage.message); }}
                className="px-4 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200">
                Copy
              </button>
            </div>
            <button onClick={() => setWaMessage(null)} className="mt-2 w-full text-center text-xs text-gray-400">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
