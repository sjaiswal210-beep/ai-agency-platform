"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

import { useEffect, useState } from "react";
import { ArrowLeft, Building2, Package, ToggleLeft, ToggleRight, Search, Filter, Save, Check, Plus } from "lucide-react";

interface Module {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  is_core: boolean;
  default_plans: string[];
}

interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  status: string;
  enabled_modules: string[];
  enabled_modules_count: number;
  created_at: string;
}

interface Template {
  id: string;
  name: string;
  icon: string;
  module_ids: string[];
}

export default function AdminPage() {
  const [modules, setModules] = useState<Module[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [enabledModules, setEnabledModules] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/admin/modules`).then(r => r.json()).then(d => setModules(d.modules || []));
    fetch(`${API_BASE}/api/admin/organizations`).then(r => r.json()).then(d => setOrganizations(d.organizations || []));
    fetch(`${API_BASE}/api/admin/templates`).then(r => r.json()).then(d => setTemplates(d.templates || []));
  }, []);

  const selectOrg = (org: Organization) => {
    setSelectedOrg(org);
    setEnabledModules(org.enabled_modules || []);
    setSaved(false);
  };

  const toggleModule = (moduleId: string) => {
    const mod = modules.find(m => m.id === moduleId);
    if (mod?.is_core) return; // Can't disable core modules
    setEnabledModules(prev =>
      prev.includes(moduleId) ? prev.filter(m => m !== moduleId) : [...prev, moduleId]
    );
    setSaved(false);
  };

  const applyTemplate = (templateId: string) => {
    const tmpl = templates.find(t => t.id === templateId);
    if (tmpl) {
      const coreIds = modules.filter(m => m.is_core).map(m => m.id);
      setEnabledModules([...new Set([...coreIds, ...tmpl.module_ids])]);
      setSaved(false);
    }
  };

  const saveModules = async () => {
    if (!selectedOrg) return;
    setSaving(true);
    try {
      await fetch(`${API_BASE}/api/admin/organizations/${selectedOrg.id}/modules`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled_modules: enabledModules }),
      });
      setSaved(true);
      // Update local state
      setOrganizations(prev => prev.map(o =>
        o.id === selectedOrg.id ? { ...o, enabled_modules: enabledModules, enabled_modules_count: enabledModules.length } : o
      ));
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const filteredOrgs = organizations.filter(o =>
    o.name.toLowerCase().includes(search.toLowerCase()) || o.slug.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <Building2 className="w-7 h-7 text-indigo-600" />
            <div>
              <h1 className="text-lg font-bold">Admin Portal</h1>
              <p className="text-xs text-gray-500">Manage organizations & module assignments</p>
            </div>
          </div>
          <div className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full font-medium">
            {organizations.length} Organizations | {modules.length} Modules
          </div>
          <a href="/admin/create" className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700 transition">
            <Plus className="w-3.5 h-3.5" /> New Organization
          </a>

        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Organizations List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="p-3 border-b border-gray-100">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
                  <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search organizations..."
                    className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
                </div>
              </div>
              <div className="max-h-[calc(100vh-240px)] overflow-y-auto">
                {filteredOrgs.map(org => (
                  <button key={org.id} onClick={() => selectOrg(org)}
                    className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition ${selectedOrg?.id === org.id ? "bg-indigo-50 border-l-2 border-l-indigo-500" : ""}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{org.name}</p>
                        <p className="text-xs text-gray-500">{org.slug}.city-maps.online</p>
                      </div>
                      <div className="text-right">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          org.plan === "enterprise" ? "bg-purple-50 text-purple-700" :
                          org.plan === "pro" ? "bg-blue-50 text-blue-700" :
                          "bg-gray-50 text-gray-600"
                        }`}>{org.plan}</span>
                        <p className="text-xs text-gray-400 mt-1">{org.enabled_modules_count} modules</p>
                      </div>
                    </div>
                  </button>
                ))}
                {filteredOrgs.length === 0 && (
                  <p className="text-center text-sm text-gray-400 py-8">No organizations found</p>
                )}
              </div>
            </div>
          </div>

          {/* Module Assignment */}
          <div className="lg:col-span-2">
            {selectedOrg ? (
              <div className="space-y-4">
                {/* Org header */}
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-bold text-gray-900">{selectedOrg.name}</h2>
                      <p className="text-sm text-gray-500">{selectedOrg.slug}.city-maps.online | Plan: {selectedOrg.plan}</p>
                    </div>
                    <button onClick={saveModules} disabled={saving || saved}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                        saved ? "bg-green-100 text-green-700" : "bg-indigo-600 text-white hover:bg-indigo-700"
                      } disabled:opacity-50`}>
                      {saved ? <><Check className="w-4 h-4" /> Saved</> : saving ? "Saving..." : <><Save className="w-4 h-4" /> Save Changes</>}
                    </button>
                  </div>

                  {/* Template quick-apply */}
                  <div className="mt-3 flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-gray-500 font-medium">Quick Apply:</span>
                    {templates.map(t => (
                      <button key={t.id} onClick={() => applyTemplate(t.id)}
                        className="text-xs px-2 py-1 rounded-full border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition">
                        {t.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Module grid */}
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Module Access Control</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {modules.map(mod => {
                      const enabled = enabledModules.includes(mod.id);
                      return (
                        <div key={mod.id}
                          className={`flex items-center justify-between p-3 rounded-lg border transition ${
                            enabled ? "border-indigo-200 bg-indigo-50/50" : "border-gray-100 bg-gray-50/50"
                          } ${mod.is_core ? "opacity-75" : "cursor-pointer hover:border-indigo-300"}`}
                          onClick={() => !mod.is_core && toggleModule(mod.id)}>
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm ${
                              enabled ? "bg-indigo-100 text-indigo-600" : "bg-gray-100 text-gray-400"
                            }`}>
                              <Package className="w-4 h-4" />
                            </div>
                            <div>
                              <p className="text-sm font-medium text-gray-900">{mod.name}</p>
                              <p className="text-xs text-gray-500">{mod.description}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {mod.is_core && <span className="text-xs text-gray-400">Core</span>}
                            {enabled ? (
                              <ToggleRight className="w-6 h-6 text-indigo-600" />
                            ) : (
                              <ToggleLeft className="w-6 h-6 text-gray-300" />
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 bg-white rounded-xl border border-gray-200">
                <div className="text-center">
                  <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">Select an organization from the left</p>
                  <p className="text-xs text-gray-400">to manage its module access</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}


