"use client";
const API_BASE = "https://ai-agency-platform.onrender.com";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Users, Receipt, Calendar, Package, Building2, CreditCard, Cpu, FolderKanban, FileText, Globe, MessageCircle, Bot, BarChart3, ChevronLeft } from "lucide-react";

const ICON_MAP: Record<string, any> = { Users, Receipt, Calendar, Package, Building2, CreditCard, Cpu, FolderKanban, FileText, Globe, MessageCircle, Bot, BarChart3 };
const MODULE_ICONS: Record<string, string> = { crm: "Users", billing: "Receipt", booking: "Calendar", inventory: "Package", property: "Building2", membership: "CreditCard", assets: "Cpu", projects: "FolderKanban", documents: "FileText", website: "Globe", whatsapp: "MessageCircle", ai_employee: "Bot", analytics: "BarChart3" };

export default function BusinessDashboard() {
  const params = useParams();
  const orgSlug = params.orgSlug as string;
  const [org, setOrg] = useState<any>(null);
  const [modules, setModules] = useState<any[]>([]);
  const [activeModule, setActiveModule] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/organizations?search=${orgSlug}`).then(r => r.json()).then(d => {
      const found = d.organizations?.find((o: any) => o.slug === orgSlug);
      if (found) { setOrg(found); fetch(`${API_BASE}/api/organizations/${found.id}/modules`).then(r => r.json()).then(m => setModules(m.modules || [])); }
    });
  }, [orgSlug]);

  const enabledModules = modules.filter((m: any) => m.enabled);
  if (!org) return <div className="min-h-screen bg-[#020817] flex items-center justify-center"><p className="text-slate-400">Loading...</p></div>;

  return (
    <div className="flex min-h-screen bg-[#020817]">
      <aside className={`${collapsed ? "w-16" : "w-56"} bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col transition-all duration-200 fixed h-full z-20`}>
        <div className="p-4 flex items-center gap-2 border-b border-white/10">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center"><Building2 className="w-5 h-5 text-white" /></div>
          {!collapsed && <span className="font-bold text-sm text-white truncate">{org.name}</span>}
        </div>
        <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
          <button onClick={() => setActiveModule(null)} className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition w-full ${!activeModule ? "bg-white/10 text-white font-medium" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}>
            <BarChart3 className="w-4 h-4" />{!collapsed && <span>Dashboard</span>}
          </button>
          {enabledModules.map((m: any) => { const Icon = ICON_MAP[MODULE_ICONS[m.module_id] || "Package"] || Package; return (
            <button key={m.module_id} onClick={() => setActiveModule(m.module_id)} className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition w-full ${activeModule === m.module_id ? "bg-white/10 text-white font-medium" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}>
              <Icon className="w-4 h-4" />{!collapsed && <span>{m.modules?.name || m.module_id}</span>}
            </button>); })}
        </nav>
        <div className="border-t border-white/10 p-2">
          <button onClick={() => setCollapsed(!collapsed)} className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-500 hover:bg-white/5 hover:text-white w-full">
            <ChevronLeft className={`w-4 h-4 transition ${collapsed ? "rotate-180" : ""}`} />{!collapsed && <span>Collapse</span>}
          </button>
        </div>
      </aside>
      <main className={`flex-1 ${collapsed ? "ml-16" : "ml-56"} transition-all duration-200 p-6`}>
        {!activeModule ? (
          <div>
            <h1 className="text-2xl font-bold mb-1">{org.name}</h1>
            <p className="text-sm text-gray-500 mb-6">{org.slug}.city-maps.online | Plan: {org.plan}</p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {enabledModules.map((m: any) => { const Icon = ICON_MAP[MODULE_ICONS[m.module_id] || "Package"] || Package; return (
                <button key={m.module_id} onClick={() => setActiveModule(m.module_id)} className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:border-indigo-300 hover:shadow-md transition">
                  <div className="flex items-center gap-3 mb-2"><div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center"><Icon className="w-5 h-5 text-indigo-600" /></div><h3 className="font-semibold text-gray-900">{m.modules?.name || m.module_id}</h3></div>
                  <p className="text-xs text-gray-500">{m.modules?.description || ""}</p>
                </button>); })}
            </div>
          </div>
        ) : (
          <div>
            <button onClick={() => setActiveModule(null)} className="text-sm text-indigo-600 hover:underline mb-4 block">&larr; Back to Dashboard</button>
            <div className="bg-white rounded-xl border border-gray-200 p-6 min-h-[60vh]">
              <h2 className="text-xl font-bold mb-2 capitalize">{activeModule.replace("_", " ")} Module</h2>
              <p className="text-sm text-gray-500 mb-4">Module active.</p><a href={`/dashboard/${orgSlug}/${activeModule}`} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">Open Full Module &rarr;</a>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}