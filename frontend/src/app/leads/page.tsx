"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

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
  lost: "bg-white/5 text-slate-400",
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string>("");
  const [qaReview, setQaReview] = useState<any>(null);
  const [qaLoading, setQaLoading] = useState<string>("");
  

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

  const handleQaReview = async (lead: Lead) => {
    setQaLoading(lead.id);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000);
      const res = await fetch(`${API_BASE}/api/qa/lead/${lead.id}`, { signal: controller.signal });
      clearTimeout(timeout);
      const data = await res.json();
      setQaReview({ ...data, business_name: lead.business_name });
    } catch (err: any) {
      if (err?.name === "AbortError") {
        alert("QA review timed out (>60s). Try again later.");
      } else {
        alert("QA review failed");
      }
    } finally {
      setQaLoading("");
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
      <header className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] border-b border-white/10 px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-slate-500 hover:text-slate-400">
              <ArrowLeft className="w-5 h-5" />
            </a>
            <Bot className="w-8 h-8 text-primary" />
            <h1 className="text-xl font-bold">Leads</h1>
            <span className="text-sm text-slate-500">({leads.length})</span>
          </div>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 border border-white/10 rounded-lg text-sm"
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
        <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl shadow-lg shadow-black/10 border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white/[0.02] border-b">
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
                  <tr key={lead.id} className={`border-b last:border-0 hover:bg-white/[0.02] border-l-4 ${
                        lead.status === "new" ? "border-l-blue-400" :
                        lead.status === "analyzed" ? "border-l-purple-400" :
                        lead.status === "outreach_sent" ? "border-l-amber-400" :
                        lead.status === "converted" ? "border-l-green-400" : "border-l-gray-200"
                      }`}>
                    <td className="px-4 py-3">
                      <p className="font-medium text-sm">{lead.business_name}</p>
                      <p className="text-xs text-slate-400 truncate max-w-[250px]">{lead.address}</p>
                    </td>
                    <td className="px-4 py-3">
                      {lead.phone ? (
                        <a href={`tel:${lead.phone}`} className="flex items-center gap-1 text-blue-600 hover:underline text-sm">
                          <Phone className="w-3 h-3" />
                          {lead.phone}
                        </a>
                      ) : (
                        <span className="text-slate-500 text-xs">No phone</span>
                      )}
                    </td>
                    <td className="px-4 py-3 capitalize text-sm">{lead.category}</td>
                    <td className="px-4 py-3">
                      {lead.rating && (
                        <span className="flex items-center gap-1 text-sm">
                          <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                          {lead.rating}
                          {lead.review_count ? <span className="text-slate-500 text-xs">({lead.review_count})</span> : null}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {lead.opportunity_score != null && (
                        <span className="font-mono text-sm">{lead.opportunity_score.toFixed(0)}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_COLORS[lead.status] || "bg-white/5"}`}>
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
          {loading && <p className="text-center py-12 text-slate-500">Loading leads...</p>}
          {!loading && leads.length === 0 && (
            <p className="text-center py-12 text-slate-500">
              No leads found. Start by discovering leads from the dashboard.
            </p>
          )}
        </div>
      </main>

      {/* QA Review Modal */}
      {qaReview && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setQaReview(null)}>
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-2xl p-6 w-full max-w-lg shadow-xl max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-lg">QA Agent Review</h3>
                <p className="text-xs text-slate-400">{qaReview.business_name}</p>
              </div>
              <div className={`text-2xl font-black ${(qaReview.overall_score || 0) >= 7 ? "text-green-600" : (qaReview.overall_score || 0) >= 5 ? "text-amber-600" : "text-red-600"}`}>
                {qaReview.overall_score || "?"}/10
              </div>
            </div>

            {qaReview.summary && (
              <p className="text-sm text-slate-400 mb-4 bg-white/[0.02] p-3 rounded-lg">{qaReview.summary}</p>
            )}

            {qaReview.scores && (
              <div className="grid grid-cols-3 gap-2 mb-4">
                {Object.entries(qaReview.scores).map(([key, val]: [string, any]) => (
                  <div key={key} className="text-center p-2 bg-white/[0.02] rounded-lg">
                    <div className={`text-lg font-bold ${val >= 7 ? "text-green-600" : val >= 5 ? "text-amber-600" : "text-red-600"}`}>{val}</div>
                    <div className="text-[10px] text-slate-400 capitalize">{key.replace("_", " ")}</div>
                  </div>
                ))}
              </div>
            )}

            {qaReview.issues && qaReview.issues.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-bold text-slate-300 uppercase mb-2">Issues Found</h4>
                <div className="space-y-2">
                  {qaReview.issues.map((issue: any, i: number) => (
                    <div key={i} className={`text-xs p-2 rounded-lg border-l-3 ${issue.severity === "high" ? "bg-red-50 border-l-red-500" : issue.severity === "medium" ? "bg-amber-50 border-l-amber-500" : "bg-blue-50 border-l-blue-500"}`}>
                      <span className="font-semibold capitalize">[{issue.area}]</span> {issue.detail}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {qaReview.fixes_needed && qaReview.fixes_needed.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-bold text-slate-300 uppercase mb-2">Fixes Applied</h4>
                <ul className="text-xs text-slate-400 space-y-1">
                  {qaReview.fixes_needed.map((fix: string, i: number) => (
                    <li key={i} className="flex items-start gap-2"><span className="text-green-500 mt-0.5">&#10003;</span> {fix}</li>
                  ))}
                </ul>
              </div>
            )}

            {qaReview.auto_fixed && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-2 text-xs text-green-700 font-medium mb-4">
                &#10003; Issues were auto-fixed by the QA agent
              </div>
            )}

            <button onClick={() => setQaReview(null)} className="w-full text-center py-2 text-xs text-slate-500 hover:text-slate-400">Close</button>
          </div>
        </div>
      )}

      
      {/* WhatsApp Message Modal */}
      {waMessage && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setWaMessage(null)}>
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-2xl p-6 w-full max-w-md shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-bold mb-1">WhatsApp Outreach</h3>
            <p className="text-xs text-slate-400 mb-3">Message for {waMessage.business}</p>
            <div className="bg-white/[0.02] rounded-lg p-3 text-sm whitespace-pre-wrap mb-4 max-h-60 overflow-y-auto border">
              {waMessage.message}
            </div>
            
                      <div className="flex gap-2">
              <a href={waMessage.link} target="_blank" rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-2 bg-green-500 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-green-600">
                Open WhatsApp
              </a>
              <button onClick={() => {navigator.clipboard.writeText(waMessage.message); }}
                className="px-4 py-2.5 bg-white/5 text-slate-400 rounded-xl text-sm font-medium hover:bg-gray-200">
                Copy
              </button>
            </div>
            <button onClick={() => setWaMessage(null)} className="mt-2 w-full text-center text-xs text-slate-500">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
