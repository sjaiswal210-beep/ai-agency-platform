"use client";
const API_BASE = "https://ai-agency-platform.onrender.com";
import { useEffect, useState } from "react";
import { ArrowLeft, Search, Smartphone, Globe } from "lucide-react";

interface Visitor {
  id: string;
  phone: string;
  org_slug: string;
  org_name: string;
  last_source: string;
  visit_count: number;
  created_at: string;
}

export default function VisitorsPage() {
  const [visitors, setVisitors] = useState<Visitor[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const load = (q = "") => {
    setLoading(true);
    let url = `${API_BASE}/api/dashboard-access/list?pwd=kalpdev2024&limit=300`;
    if (q) url += `&search=${encodeURIComponent(q)}`;
    fetch(url).then(r => r.json()).then(d => { setVisitors(d.visitors || []); setLoading(false); }).catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/admin" className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <Smartphone className="w-6 h-6 text-indigo-600" />
            <div>
              <h1 className="text-lg font-bold">Dashboard Visitors</h1>
              <p className="text-xs text-gray-500">{visitors.length} numbers captured</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="relative max-w-sm mb-4">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load(search)}
            placeholder="Search by phone... (Enter)"
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
        </div>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Phone</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Business</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Website</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Source</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Visits</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">First Opened</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="text-center py-8 text-gray-400">Loading...</td></tr>
              ) : visitors.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-8 text-gray-400">No visitors yet</td></tr>
              ) : visitors.map(v => (
                <tr key={v.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    <a href={`https://wa.me/91${v.phone.slice(-10)}`} target="_blank" className="text-green-600 hover:underline">{v.phone}</a>
                  </td>
                  <td className="px-4 py-3 text-gray-700">{v.org_name || "-"}</td>
                  <td className="px-4 py-3">
                    <a href={`https://${v.org_slug}.city-maps.online`} target="_blank" className="text-indigo-600 hover:underline flex items-center gap-1">
                      <Globe className="w-3 h-3" />{v.org_slug}
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${v.last_source === "app" ? "bg-green-50 text-green-700" : "bg-blue-50 text-blue-700"}`}>{v.last_source}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{v.visit_count}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{new Date(v.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}