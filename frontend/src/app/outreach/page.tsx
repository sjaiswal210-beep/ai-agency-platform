"use client";

import { useEffect, useState } from "react";
import { api, Lead } from "@/lib/api";
import { Bot, Mail, MessageCircle, ArrowLeft } from "lucide-react";

interface OutreachItem {
  id: string;
  lead_id: string;
  channel: string;
  message: string;
  status: string;
  sent_at?: string;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  sent: "bg-blue-100 text-blue-700",
  delivered: "bg-indigo-100 text-indigo-700",
  read: "bg-purple-100 text-purple-700",
  replied: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function OutreachPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<string>("");
  const [messages, setMessages] = useState<OutreachItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.leads
      .list()
      .then((data) => {
        setLeads(data);
        setLoading(false);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedLead) {
      api.outreach
        .history(selectedLead)
        .then((data) => setMessages(data as OutreachItem[]))
        .catch(console.error);
    }
  }, [selectedLead]);

  return (
    <div className="min-h-screen">
      <header className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] border-b border-white/10 px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-slate-500 hover:text-slate-400">
              <ArrowLeft className="w-5 h-5" />
            </a>
            <Bot className="w-8 h-8 text-primary" />
            <h1 className="text-xl font-bold">Outreach</h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lead list */}
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl shadow-lg shadow-black/10 border border-white/5 overflow-hidden">
            <div className="p-4 border-b bg-[#020817]">
              <h2 className="font-semibold text-sm">Select a Lead</h2>
            </div>
            <div className="max-h-[600px] overflow-y-auto">
              {leads.map((lead) => (
                <button
                  key={lead.id}
                  onClick={() => setSelectedLead(lead.id)}
                  className={`w-full text-left px-4 py-3 border-b last:border-0 hover:bg-white/[0.02] transition ${
                    selectedLead === lead.id ? "bg-primary/5 border-l-2 border-l-primary" : ""
                  }`}
                >
                  <p className="font-medium text-sm">{lead.business_name}</p>
                  <p className="text-xs text-slate-500">{lead.status}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Messages */}
          <div className="lg:col-span-2 bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl shadow-lg shadow-black/10 border border-white/5 overflow-hidden">
            <div className="p-4 border-b bg-[#020817]">
              <h2 className="font-semibold text-sm">
                {selectedLead ? "Message History" : "Select a lead to view messages"}
              </h2>
            </div>
            <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
              {messages.length === 0 && selectedLead && (
                <p className="text-center text-slate-500 py-8">No messages sent to this lead yet.</p>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className="border border-white/5 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {msg.channel === "email" ? (
                        <Mail className="w-4 h-4 text-blue-500" />
                      ) : (
                        <MessageCircle className="w-4 h-4 text-green-500" />
                      )}
                      <span className="text-sm font-medium capitalize">{msg.channel}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_COLORS[msg.status] || ""}`}>
                      {msg.status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 whitespace-pre-wrap">{msg.message}</p>
                  <p className="text-xs text-slate-500 mt-2">
                    {new Date(msg.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
