"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

import { useEffect, useState } from "react";
import { ArrowLeft, Building2, Plus, Check, Sparkles, Globe } from "lucide-react";

interface Template {
  id: string;
  name: string;
  icon: string;
  description: string;
  module_ids: string[];
  category: string;
}

export default function CreateOrganizationPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [city, setCity] = useState("");
  const [plan, setPlan] = useState("starter");
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/admin/templates`)
      .then(r => r.json())
      .then(d => setTemplates(d.templates || []))
      .catch(console.error);
  }, []);

  // Auto-generate slug from name
  useEffect(() => {
    if (name && !created) {
      const generated = name
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "")
        .replace(/\s+/g, "-")
        .replace(/-+/g, "-")
        .slice(0, 30);
      setSlug(generated);
    }
  }, [name]);

  const handleCreate = async () => {
    if (!name || !slug) {
      setError("Business name and slug are required");
      return;
    }
    setCreating(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/organizations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          slug,
          phone: phone || undefined,
          email: email || undefined,
          city: city || undefined,
          plan,
          template_id: selectedTemplate || undefined,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setCreated(data.organization);
      } else {
        setError(data.detail || "Failed to create organization");
      }
    } catch (e) {
      setError("Network error. Try again.");
    } finally {
      setCreating(false);
    }
  };

  if (created) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Organization Created!</h1>
          <p className="text-sm text-gray-500 mb-6">{created.name} is ready to go.</p>

          <div className="bg-gray-50 rounded-xl p-4 mb-6 text-left space-y-2">
            <div className="flex justify-between">
              <span className="text-xs text-gray-500">Subdomain</span>
              <span className="text-xs font-medium text-indigo-600">{created.slug}.city-maps.online</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-500">Plan</span>
              <span className="text-xs font-medium capitalize">{created.plan}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-500">Org ID</span>
              <span className="text-xs font-mono text-gray-600">{created.id?.slice(0, 8)}...</span>
            </div>
          </div>

          <div className="space-y-2">
            <a href={`/dashboard/${created.slug}`}
              className="block w-full py-3 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition">
              Open Business Dashboard
            </a>
            <a href="/admin"
              className="block w-full py-3 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 transition">
              Go to Admin Portal
            </a>
            <button onClick={() => { setCreated(null); setStep(1); setName(""); setSlug(""); setPhone(""); setEmail(""); setCity(""); setSelectedTemplate(""); }}
              className="block w-full py-3 text-gray-500 text-sm hover:text-gray-700 transition">
              Create Another Organization
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center gap-3 max-w-3xl mx-auto">
          <a href="/admin" className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
          <Plus className="w-6 h-6 text-indigo-600" />
          <div>
            <h1 className="text-lg font-bold">Create Organization</h1>
            <p className="text-xs text-gray-500">Set up a new business on the platform</p>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${step >= 1 ? "bg-indigo-100 text-indigo-700" : "bg-gray-100 text-gray-500"}`}>
            <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs">1</span>
            Business Info
          </div>
          <div className="w-8 h-px bg-gray-300" />
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${step >= 2 ? "bg-indigo-100 text-indigo-700" : "bg-gray-100 text-gray-500"}`}>
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${step >= 2 ? "bg-indigo-600 text-white" : "bg-gray-300 text-white"}`}>2</span>
            Choose Template
          </div>
          <div className="w-8 h-px bg-gray-300" />
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${step >= 3 ? "bg-indigo-100 text-indigo-700" : "bg-gray-100 text-gray-500"}`}>
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${step >= 3 ? "bg-indigo-600 text-white" : "bg-gray-300 text-white"}`}>3</span>
            Confirm
          </div>
        </div>

        {/* Step 1: Business Info */}
        {step === 1 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Business Information</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Business Name *</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Sunrise PG, ABC Gym, Dr. Sharma Clinic"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-300" />
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Subdomain (URL slug) *</label>
                <div className="flex items-center">
                  <input type="text" value={slug} onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))}
                    className="flex-1 px-4 py-2.5 border border-gray-200 rounded-l-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-300" />
                  <span className="px-3 py-2.5 bg-gray-50 border border-l-0 border-gray-200 rounded-r-lg text-xs text-gray-500">.city-maps.online</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Phone</label>
                  <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)}
                    placeholder="9876543210"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    placeholder="business@example.com"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">City</label>
                  <input type="text" value={city} onChange={(e) => setCity(e.target.value)}
                    placeholder="e.g., Pune, Mumbai, Bangalore"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Plan</label>
                  <select value={plan} onChange={(e) => setPlan(e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 bg-white">
                    <option value="starter">Starter (Basic modules)</option>
                    <option value="pro">Pro (Most modules)</option>
                    <option value="enterprise">Enterprise (All modules)</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button onClick={() => { if (name && slug) setStep(2); else setError("Name and slug are required"); }}
                disabled={!name || !slug}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
                Next: Choose Template &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Choose Template */}
        {step === 2 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-1">Choose Industry Template</h2>
            <p className="text-sm text-gray-500 mb-4">This pre-selects the right modules for the business type. You can change later.</p>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-6">
              {/* No template option */}
              <button onClick={() => setSelectedTemplate("")}
                className={`p-3 rounded-xl border text-center transition ${!selectedTemplate ? "border-indigo-300 bg-indigo-50 ring-2 ring-indigo-200" : "border-gray-200 hover:border-gray-300"}`}>
                <div className="text-2xl mb-1">⚙️</div>
                <p className="text-xs font-medium text-gray-700">Custom</p>
                <p className="text-[10px] text-gray-400">Core modules only</p>
              </button>

              {templates.map(t => (
                <button key={t.id} onClick={() => setSelectedTemplate(t.id)}
                  className={`p-3 rounded-xl border text-center transition ${selectedTemplate === t.id ? "border-indigo-300 bg-indigo-50 ring-2 ring-indigo-200" : "border-gray-200 hover:border-gray-300"}`}>
                  <div className="text-2xl mb-1">{
                    t.id === "pg_hostel" ? "🏠" :
                    t.id === "restaurant" ? "🍽️" :
                    t.id === "salon_spa" ? "💇" :
                    t.id === "gym_fitness" ? "🏋️" :
                    t.id === "photographer" ? "📷" :
                    t.id === "solar_company" ? "☀️" :
                    t.id === "doctor_clinic" ? "🩺" :
                    t.id === "school_coaching" ? "🎓" :
                    t.id === "real_estate" ? "🏡" :
                    t.id === "freelancer" ? "💻" :
                    t.id === "kirana_retail" ? "🛒" :
                    t.id === "hotel_resort" ? "🏨" :
                    t.id === "contractor" ? "🔨" :
                    t.id === "lawyer_ca" ? "⚖️" : "📦"
                  }</div>
                  <p className="text-xs font-medium text-gray-700">{t.name}</p>
                  <p className="text-[10px] text-gray-400">{t.module_ids?.length || 0} modules</p>
                </button>
              ))}
            </div>

            {selectedTemplate && (
              <div className="bg-indigo-50 rounded-lg p-3 mb-4">
                <p className="text-xs font-medium text-indigo-700 mb-1">Modules that will be enabled:</p>
                <div className="flex flex-wrap gap-1">
                  {templates.find(t => t.id === selectedTemplate)?.module_ids.map(m => (
                    <span key={m} className="px-2 py-0.5 bg-white rounded-full text-xs text-indigo-600 border border-indigo-200 capitalize">{m.replace("_", " ")}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-between">
              <button onClick={() => setStep(1)} className="px-4 py-2.5 text-gray-600 text-sm hover:text-gray-800">
                &larr; Back
              </button>
              <button onClick={() => setStep(3)}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition">
                Next: Confirm &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Confirm */}
        {step === 3 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Confirm & Create</h2>

            <div className="bg-gray-50 rounded-xl p-5 space-y-3 mb-6">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Business Name</span>
                <span className="text-sm font-medium">{name}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Subdomain</span>
                <span className="text-sm font-medium text-indigo-600">{slug}.city-maps.online</span>
              </div>
              {phone && <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Phone</span>
                <span className="text-sm font-medium">{phone}</span>
              </div>}
              {email && <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Email</span>
                <span className="text-sm font-medium">{email}</span>
              </div>}
              {city && <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">City</span>
                <span className="text-sm font-medium">{city}</span>
              </div>}
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Plan</span>
                <span className="text-sm font-medium capitalize">{plan}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Template</span>
                <span className="text-sm font-medium">{selectedTemplate ? templates.find(t => t.id === selectedTemplate)?.name : "Custom (core only)"}</span>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <div className="flex justify-between">
              <button onClick={() => setStep(2)} className="px-4 py-2.5 text-gray-600 text-sm hover:text-gray-800">
                &larr; Back
              </button>
              <button onClick={handleCreate} disabled={creating}
                className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg text-sm font-medium hover:shadow-lg hover:shadow-indigo-500/25 disabled:opacity-50 transition flex items-center gap-2">
                {creating ? "Creating..." : <><Sparkles className="w-4 h-4" /> Create Organization</>}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
