"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

import { useEffect, useState } from "react";
import { api, DashboardStats } from "@/lib/api";
import { ArrowLeft, Bot, DollarSign, Zap, Search, RefreshCw } from "lucide-react";

interface UsageItem {
  action: string;
  calls: number;
  cost_per_call: number;
  total_cost: number;
}

interface UsageData {
  items: UsageItem[];
  total_cost: number;
  total_google_cost: number;
  total_gemini_cost: number;
  google_free_remaining: number;
  gemini_free: boolean;
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [replicateUsage, setReplicateUsage] = useState<any>(null);

  const USD_TO_INR = 85;

  const fetchData = () => {
    api.dashboard.stats().then(setStats).catch(console.error);
    fetch(`${API_BASE}/api/dashboard/usage`).then(r => r.json()).then(setUsage).catch(console.error);
    fetch(`${API_BASE}/api/dashboard/replicate-usage`).then(r => r.json()).then(setReplicateUsage).catch(console.error);
  };

  useEffect(() => { fetchData(); }, []);

  const totalLeads = stats?.total_leads ?? 0;
  const totalWebsites = stats?.total_websites ?? 0;
  const totalOutreach = stats?.total_outreach ?? 0;

  const resetUsage = async () => {
    await fetch(`${API_BASE}/api/dashboard/usage/reset`, { method: "POST" });
    fetchData();
  };

  return (
    <div className="min-h-screen bg-[#020817]">
      <header className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] border-b border-white/10 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-slate-400 hover:text-slate-300"><ArrowLeft className="w-5 h-5" /></a>
            <Bot className="w-7 h-7 text-primary" />
            <h1 className="text-lg font-bold text-white">Analytics & Costs</h1>
          </div>
          <div className="flex gap-2">
            <button onClick={fetchData} className="flex items-center gap-1 px-3 py-1.5 text-xs bg-white/5 rounded-lg hover:bg-white/10">
              <RefreshCw className="w-3 h-3" /> Refresh
            </button>
            <button onClick={resetUsage} className="flex items-center gap-1 px-3 py-1.5 text-xs text-red-500 bg-red-50 rounded-lg hover:bg-red-100">
              Reset Counters
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Cost summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl border border-white/5 p-5">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-4 h-4 text-green-500" />
              <span className="text-xs font-medium text-slate-300">Total Spend</span>
            </div>
            <p className="text-2xl font-bold text-white">{String.fromCharCode(8377)}{((usage?.total_cost ?? 0) * USD_TO_INR).toFixed(2)}</p>
            <p className="text-xs text-slate-400 mt-1">This session</p>
          </div>
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl border border-white/5 p-5">
            <div className="flex items-center gap-2 mb-2">
              <Search className="w-4 h-4 text-blue-500" />
              <span className="text-xs font-medium text-slate-300">Google Places</span>
            </div>
            <p className="text-2xl font-bold text-white">{String.fromCharCode(8377)}{((usage?.total_google_cost ?? 0) * USD_TO_INR).toFixed(2)}</p>
            <p className="text-xs text-green-600 mt-1">{String.fromCharCode(8377)}{((usage?.google_free_remaining ?? 200) * USD_TO_INR).toFixed(0)} free remaining</p>
          </div>
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl border border-white/5 p-5">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-medium text-slate-300">Gemini AI</span>
            </div>
            <p className="text-2xl font-bold text-white">{String.fromCharCode(8377)}{((usage?.total_gemini_cost ?? 0) * USD_TO_INR).toFixed(2)}</p>
            <p className="text-xs text-green-600 mt-1">{usage?.gemini_free ? "Within free tier" : "Paid usage"}</p>
          </div>
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl border border-white/5 p-5">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-4 h-4 text-primary" />
              <span className="text-xs font-medium text-slate-300">Cost Per Lead</span>
            </div>
            <p className="text-2xl font-bold text-white">{String.fromCharCode(8377)}{totalLeads > 0 ? (((usage?.total_cost ?? 0) * USD_TO_INR) / totalLeads).toFixed(2) : "0.00"}</p>
            <p className="text-xs text-slate-400 mt-1">{totalLeads} leads total</p>
          </div>
        </div>

        {/* Live usage table */}
        <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl border border-white/5 overflow-hidden mb-6">
          <div className="p-4 border-b border-white/5">
            <h2 className="font-semibold text-sm text-white">Live API Usage (This Session)</h2>
          </div>
          <table className="w-full text-sm text-slate-300">
            <thead className="bg-[#020817]">
              <tr>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-300">API Action</th>
                <th className="text-right px-4 py-2.5 text-xs font-medium text-slate-300">Calls</th>
                <th className="text-right px-4 py-2.5 text-xs font-medium text-slate-300">Cost/Call</th>
                <th className="text-right px-4 py-2.5 text-xs font-medium text-slate-300">Total Cost</th>
              </tr>
            </thead>
            <tbody>
              {usage?.items.map((item, i) => (
                <tr key={i} className={`border-t border-white/5 ${item.calls > 0 ? "bg-white/[0.03]" : "bg-white/[0.02]/50 opacity-60"}`}>
                  <td className="px-4 py-2.5 capitalize">{item.action.replace(/_/g, " ")}</td>
                  <td className="px-4 py-2.5 text-right font-mono">{item.calls}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-xs text-slate-300">{String.fromCharCode(8377)}{(item.cost_per_call * USD_TO_INR).toFixed(2)}</td>
                  <td className="px-4 py-2.5 text-right font-mono font-medium">{String.fromCharCode(8377)}{(item.total_cost * USD_TO_INR).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-white/[0.02] border-t-2 border-white/10">
              <tr>
                <td className="px-4 py-3 font-bold" colSpan={3}>Total</td>
                <td className="px-4 py-3 text-right font-mono font-bold text-primary">{String.fromCharCode(8377)}{((usage?.total_cost ?? 0) * USD_TO_INR).toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* Two columns */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Pipeline */}
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl border border-white/5 p-5">
            <h3 className="font-semibold text-sm mb-4 text-white">Pipeline Funnel</h3>
            <div className="space-y-3">
              {[
                { label: "Discovered", count: totalLeads, color: "bg-blue-500" },
                { label: "Analyzed", count: Number(stats?.leads_by_status?.analyzed || 0), color: "bg-purple-500" },
                { label: "Outreach Sent", count: Number(stats?.leads_by_status?.outreach_sent || 0), color: "bg-amber-500" },
                { label: "Websites Made", count: totalWebsites, color: "bg-indigo-500" },
                { label: "Converted", count: Number(stats?.leads_by_status?.converted || 0), color: "bg-green-500" },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-300">{item.label}</span>
                    <span className="font-medium">{item.count}</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className={`h-full ${item.color} rounded-full`} style={{ width: `${totalLeads ? Math.max((item.count / totalLeads) * 100, item.count > 0 ? 5 : 0) : 0}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Replicate Video costs */}
          <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl border border-white/5 p-5">
            <h3 className="font-semibold text-sm mb-4 text-white">API Pricing & Free Tiers</h3>
            <div className="space-y-4 text-xs">
              <div>
                <p className="font-medium text-slate-300 mb-1">Google Places API</p>
                <ul className="space-y-1 text-slate-300">
                  <li className="flex justify-between"><span>Text Search</span><span className="font-mono">$32 / 1000 calls</span></li>
                  <li className="flex justify-between"><span>Place Details</span><span className="font-mono">$17 / 1000 calls</span></li>
                  <li className="flex justify-between"><span>Place Photos</span><span className="font-mono">$7 / 1000 calls</span></li>
                  <li className="flex justify-between text-green-600 font-medium"><span>Free credit</span><span>$200/month</span></li>
                  <li className="flex justify-between text-green-600"><span>= approx</span><span>~4000 leads free</span></li>
                </ul>
              </div>
              <div>
                <p className="font-medium text-slate-300 mb-1">Google Gemini API</p>
                <ul className="space-y-1 text-slate-300">
                  <li className="flex justify-between"><span>Input tokens</span><span className="font-mono">$0.075 / 1M</span></li>
                  <li className="flex justify-between"><span>Output tokens</span><span className="font-mono">$0.30 / 1M</span></li>
                  <li className="flex justify-between text-green-600 font-medium"><span>Free tier</span><span>15 req/min</span></li>
                  <li className="flex justify-between text-green-600"><span>Daily limit</span><span>1M tokens free</span></li>
                </ul>
              </div>
              <div>
                <p className="font-medium text-slate-300 mb-1">Supabase</p>
                <ul className="space-y-1 text-slate-300">
                  <li className="flex justify-between text-green-600 font-medium"><span>Database</span><span>Free (500MB)</span></li>
                  <li className="flex justify-between text-green-600"><span>API requests</span><span>Unlimited</span></li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom note */}
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
          <p className="text-sm text-green-400 font-medium">
            With free tiers, you can run ~4000 lead discoveries + unlimited AI operations per month at $0 cost.
          </p>
        </div>
      </main>
    </div>
  );
}
