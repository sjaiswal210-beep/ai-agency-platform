"use client";
const API_BASE = "https://ai-agency-platform.onrender.com";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Users, Plus, Search, Phone, Mail, Tag, Filter, ChevronRight, ArrowLeft, MoreVertical, MessageCircle, Calendar, FileText, X } from "lucide-react";

interface Contact {
  id: string;
  name: string;
  email: string;
  phone: string;
  company: string;
  type: string;
  stage: string;
  score: number;
  tags: string[];
  source: string;
  last_contacted_at: string;
  created_at: string;
}

interface Activity {
  id: string;
  type: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
}

const STAGE_COLORS: Record<string, string> = {
  new: "bg-blue-100 text-blue-700",
  contacted: "bg-yellow-100 text-yellow-700",
  qualified: "bg-purple-100 text-purple-700",
  proposal: "bg-orange-100 text-orange-700",
  won: "bg-green-100 text-green-700",
  lost: "bg-red-100 text-red-700",
};

const TYPE_COLORS: Record<string, string> = {
  lead: "bg-blue-50 text-blue-600",
  customer: "bg-green-50 text-green-600",
  vendor: "bg-amber-50 text-amber-600",
  partner: "bg-purple-50 text-purple-600",
  employee: "bg-gray-50 text-gray-600",
};

export default function CRMPage() {
  const params = useParams();
  const orgSlug = params.orgSlug as string;
  const [orgId, setOrgId] = useState("");
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selected, setSelected] = useState<Contact | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStage, setFilterStage] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [showActivity, setShowActivity] = useState(false);
  const [loading, setLoading] = useState(true);

  // New contact form
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newType, setNewType] = useState("lead");
  const [newCompany, setNewCompany] = useState("");
  const [newSource, setNewSource] = useState("");

  // New activity form
  const [actType, setActType] = useState("note");
  const [actTitle, setActTitle] = useState("");
  const [actDesc, setActDesc] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/organizations?search=${orgSlug}`)
      .then(r => r.json())
      .then(d => {
        const found = d.organizations?.find((o: any) => o.slug === orgSlug);
        if (found) { setOrgId(found.id); loadContacts(found.id); }
      });
  }, [orgSlug]);

  const loadContacts = (oid?: string) => {
    const id = oid || orgId;
    if (!id) return;
    setLoading(true);
    let url = `${API_BASE}/api/org/${id}/crm/contacts?limit=100`;
    if (filterType) url += `&type=${filterType}`;
    if (filterStage) url += `&stage=${filterStage}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    fetch(url).then(r => r.json()).then(d => { setContacts(d.contacts || []); setLoading(false); }).catch(() => setLoading(false));
  };

  useEffect(() => { if (orgId) loadContacts(); }, [filterType, filterStage]);

  const searchContacts = () => { if (orgId) loadContacts(); };

  const selectContact = (c: Contact) => {
    setSelected(c);
    fetch(`${API_BASE}/api/org/${orgId}/crm/contacts/${c.id}/activities`)
      .then(r => r.json())
      .then(d => setActivities(d.activities || []));
  };

  const addContact = async () => {
    if (!newName) return;
    await fetch(`${API_BASE}/api/org/${orgId}/crm/contacts`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName, phone: newPhone, email: newEmail, type: newType, company: newCompany, source: newSource }),
    });
    setShowAdd(false); setNewName(""); setNewPhone(""); setNewEmail(""); setNewCompany(""); setNewSource("");
    loadContacts();
  };

  const addActivity = async () => {
    if (!selected || !actTitle) return;
    await fetch(`${API_BASE}/api/org/${orgId}/crm/contacts/${selected.id}/activities`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: actType, title: actTitle, description: actDesc }),
    });
    setShowActivity(false); setActTitle(""); setActDesc("");
    // Reload activities
    fetch(`${API_BASE}/api/org/${orgId}/crm/contacts/${selected.id}/activities`)
      .then(r => r.json()).then(d => setActivities(d.activities || []));
  };

  const updateStage = async (contactId: string, stage: string) => {
    await fetch(`${API_BASE}/api/org/${orgId}/crm/contacts/${contactId}`, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage }),
    });
    loadContacts();
    if (selected?.id === contactId) setSelected({ ...selected, stage });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href={`/dashboard/${orgSlug}`} className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <Users className="w-6 h-6 text-indigo-600" />
            <div>
              <h1 className="text-lg font-bold">CRM</h1>
              <p className="text-xs text-gray-500">{contacts.length} contacts</p>
            </div>
          </div>
          <button onClick={() => setShowAdd(true)} className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700">
            <Plus className="w-3.5 h-3.5" /> Add Contact
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <div className="relative flex-1 max-w-xs">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
            <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && searchContacts()}
              placeholder="Search name, phone, email..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
          </div>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white">
            <option value="">All Types</option>
            <option value="lead">Leads</option>
            <option value="customer">Customers</option>
            <option value="vendor">Vendors</option>
            <option value="partner">Partners</option>
          </select>
          <select value={filterStage} onChange={(e) => setFilterStage(e.target.value)} className="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white">
            <option value="">All Stages</option>
            <option value="new">New</option>
            <option value="contacted">Contacted</option>
            <option value="qualified">Qualified</option>
            <option value="proposal">Proposal</option>
            <option value="won">Won</option>
            <option value="lost">Lost</option>
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ minHeight: "calc(100vh - 180px)" }}>
          {/* Contact List */}
          <div className="lg:col-span-1 bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="max-h-[calc(100vh-220px)] overflow-y-auto">
              {loading ? (
                <p className="text-center text-sm text-gray-400 py-8">Loading...</p>
              ) : contacts.length === 0 ? (
                <div className="text-center py-12 px-4">
                  <Users className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No contacts yet</p>
                  <button onClick={() => setShowAdd(true)} className="mt-2 text-xs text-indigo-600 hover:underline">Add your first contact</button>
                </div>
              ) : contacts.map(c => (
                <button key={c.id} onClick={() => selectContact(c)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition ${selected?.id === c.id ? "bg-indigo-50 border-l-2 border-l-indigo-500" : ""}`}>
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">{c.name}</p>
                      <p className="text-xs text-gray-500 truncate">{c.phone || c.email || c.company || "No details"}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1 ml-2">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${STAGE_COLORS[c.stage] || "bg-gray-100 text-gray-600"}`}>{c.stage}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${TYPE_COLORS[c.type] || "bg-gray-50 text-gray-500"}`}>{c.type}</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Contact Detail */}
          <div className="lg:col-span-2">
            {selected ? (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{selected.name}</h2>
                    <div className="flex items-center gap-3 mt-1">
                      {selected.phone && <span className="flex items-center gap-1 text-xs text-gray-500"><Phone className="w-3 h-3" />{selected.phone}</span>}
                      {selected.email && <span className="flex items-center gap-1 text-xs text-gray-500"><Mail className="w-3 h-3" />{selected.email}</span>}
                    </div>
                    {selected.company && <p className="text-xs text-gray-400 mt-1">{selected.company}</p>}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${TYPE_COLORS[selected.type]}`}>{selected.type}</span>
                  </div>
                </div>

                {/* Stage pipeline */}
                <div className="flex items-center gap-1 mb-6 overflow-x-auto pb-1">
                  {["new", "contacted", "qualified", "proposal", "won", "lost"].map(stage => (
                    <button key={stage} onClick={() => updateStage(selected.id, stage)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium transition whitespace-nowrap ${
                        selected.stage === stage ? STAGE_COLORS[stage] : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                      }`}>{stage}</button>
                  ))}
                </div>

                {/* Tags */}
                {selected.tags && selected.tags.length > 0 && (
                  <div className="flex items-center gap-1 mb-4">
                    <Tag className="w-3 h-3 text-gray-400" />
                    {selected.tags.map(t => <span key={t} className="text-xs px-2 py-0.5 bg-gray-100 rounded-full">{t}</span>)}
                  </div>
                )}

                {/* Activity Timeline */}
                <div className="border-t border-gray-100 pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-gray-700">Activity Timeline</h3>
                    <button onClick={() => setShowActivity(true)} className="text-xs text-indigo-600 hover:underline flex items-center gap-1">
                      <Plus className="w-3 h-3" /> Add Activity
                    </button>
                  </div>

                  {activities.length === 0 ? (
                    <p className="text-xs text-gray-400 text-center py-4">No activities yet</p>
                  ) : (
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {activities.map(a => (
                        <div key={a.id} className="flex gap-3">
                          <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                            a.type === "call" ? "bg-green-100" : a.type === "meeting" ? "bg-blue-100" : a.type === "note" ? "bg-yellow-100" : "bg-gray-100"
                          }`}>
                            {a.type === "call" ? <Phone className="w-3 h-3 text-green-600" /> :
                             a.type === "meeting" ? <Calendar className="w-3 h-3 text-blue-600" /> :
                             a.type === "whatsapp" ? <MessageCircle className="w-3 h-3 text-green-600" /> :
                             <FileText className="w-3 h-3 text-yellow-600" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-800">{a.title || a.type}</p>
                            {a.description && <p className="text-xs text-gray-500 mt-0.5">{a.description}</p>}
                            <p className="text-[10px] text-gray-400 mt-1">{new Date(a.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full bg-white rounded-xl border border-gray-200">
                <div className="text-center py-16">
                  <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">Select a contact to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Add Contact Modal */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowAdd(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Add Contact</h2>
              <button onClick={() => setShowAdd(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Name *</label>
                <input type="text" value={newName} onChange={e => setNewName(e.target.value)} placeholder="Contact name"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Phone</label>
                  <input type="tel" value={newPhone} onChange={e => setNewPhone(e.target.value)} placeholder="9876543210"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Email</label>
                  <input type="email" value={newEmail} onChange={e => setNewEmail(e.target.value)} placeholder="email@example.com"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Type</label>
                  <select value={newType} onChange={e => setNewType(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
                    <option value="lead">Lead</option>
                    <option value="customer">Customer</option>
                    <option value="vendor">Vendor</option>
                    <option value="partner">Partner</option>
                    <option value="employee">Employee</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Source</label>
                  <input type="text" value={newSource} onChange={e => setNewSource(e.target.value)} placeholder="Google, Referral..."
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Company</label>
                <input type="text" value={newCompany} onChange={e => setNewCompany(e.target.value)} placeholder="Company name"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
              </div>
              <button onClick={addContact} disabled={!newName}
                className="w-full mt-2 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
                Add Contact
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Activity Modal */}
      {showActivity && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowActivity(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Add Activity</h2>
              <button onClick={() => setShowActivity(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Type</label>
                <div className="flex gap-2">
                  {["note", "call", "meeting", "task", "email", "whatsapp"].map(t => (
                    <button key={t} onClick={() => setActType(t)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${actType === t ? "bg-indigo-100 border-indigo-300 text-indigo-700" : "border-gray-200 text-gray-600 hover:border-gray-300"}`}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Title *</label>
                <input type="text" value={actTitle} onChange={e => setActTitle(e.target.value)} placeholder="e.g., Follow-up call, Sent quotation"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Notes</label>
                <textarea value={actDesc} onChange={e => setActDesc(e.target.value)} placeholder="Activity details..."
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 h-20 resize-none" />
              </div>
              <button onClick={addActivity} disabled={!actTitle}
                className="w-full mt-2 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
                Add Activity
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}