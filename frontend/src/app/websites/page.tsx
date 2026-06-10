"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://ai-agency-platform.onrender.com" : "http://localhost:8000");

import { useEffect, useState } from "react";
import { Bot, Globe, ExternalLink, ArrowLeft, Phone, MapPin } from "lucide-react";

interface WebsiteItem {
  id: string;
  lead_id: string;
  template: string;
  status: string;
  created_at: string;
  slug?: string;
  business_name?: string;
  category?: string;
  phone?: string;
  address?: string;
}

const STATUS_COLORS: Record<string, string> = {
  generating: "bg-yellow-100 text-yellow-700",
  preview: "bg-blue-100 text-blue-700",
  approved: "bg-green-100 text-green-700",
  deployed: "bg-emerald-200 text-emerald-800",
};

export default function WebsitesPage() {
  const [websites, setWebsites] = useState<WebsiteItem[]>([]);
  const [loading, setLoading] = useState(true);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete website for ${name}?`)) return;
    try {
      await fetch(`${API_BASE}/api/leads/website/${id}`, { method: "DELETE" });
      setWebsites(websites.filter(w => w.id !== id));
    } catch (err) { console.error(err); }
  };

  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    fetch(`${API_BASE}/api/websites/`)
      .then((r) => {
        if (!r.ok) throw new Error(`Server error: ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setWebsites(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not load websites. The server may be starting up — try refreshing in 30 seconds.");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 px-6 py-3 sticky top-0 z-10">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-gray-600">
              <ArrowLeft className="w-5 h-5" />
            </a>
            <Bot className="w-7 h-7 text-primary" />
            <h1 className="text-lg font-bold">Generated Websites</h1>
            <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{websites.length}</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {loading ? (
          <p className="text-center py-20 text-gray-400">Loading...</p>
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-500 text-sm mb-2">{error}</p>
            <button onClick={() => window.location.reload()} className="px-4 py-2 bg-primary text-white rounded-lg text-sm">Retry</button>
          </div>
        ) : websites.length === 0 ? (
          <p className="text-center py-20 text-gray-400">No websites generated yet. Go to Leads and click "Site" to create one.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {websites.map((site) => (
              <div key={site.id} className="bg-white rounded-xl border border-gray-100 overflow-hidden hover-lift">
                {/* Preview thumbnail */}
                <div className="relative h-40 bg-gray-100 overflow-hidden border-b">
                  <iframe
                    src={site.slug ? `${API_BASE}/api/preview/by-slug/${site.slug}` : `${API_BASE}/api/preview/${site.id}`}
                    className="w-full h-full border-0 pointer-events-none"
                    style={{ transform: "scale(0.4)", transformOrigin: "top left", width: "250%", height: "250%" }}
                    title={site.business_name || site.template}
                  />
                </div>

                {/* Card content */}
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-sm truncate">{site.business_name || "Untitled"}</h3>
                      <p className="text-xs text-gray-500 capitalize">{site.category || site.template}</p>
                      {site.slug && <p className="text-xs text-purple-500 truncate">{site.slug}.city-maps.online</p>}
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-xs flex-shrink-0 ml-2 ${STATUS_COLORS[site.status] || "bg-gray-100 text-gray-600"}`}>
                      {site.status}
                    </span>
                  </div>

                  {/* Info */}
                  <div className="space-y-1 mb-3">
                    {site.phone && (
                      <p className="text-xs text-gray-500 flex items-center gap-1">
                        <Phone className="w-3 h-3" /> {site.phone}
                      </p>
                    )}
                    {site.address && (
                      <p className="text-xs text-gray-500 flex items-center gap-1 truncate">
                        <MapPin className="w-3 h-3 flex-shrink-0" /> {site.address.split(",").slice(0, 2).join(",")}
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <a
                      href={site.slug ? `https://${site.slug}.city-maps.online` : `${API_BASE}/api/preview/${site.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-primary text-white text-xs font-medium rounded-lg hover:bg-primary-dark transition"
                    >
                      <ExternalLink className="w-3 h-3" /> {site.slug ? "Live Site" : "Preview"}
                    </a>
                    <a
                      href={`${API_BASE}/api/logo-gen/${site.id}/preview`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-2 bg-gray-100 text-gray-600 text-xs rounded-lg hover:bg-gray-200 transition"
                      title="Edit Logo"
                    >
                      Logo
                    </a>
                    <a
                      href={`${API_BASE}/api/panel/${site.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-2 bg-gray-100 text-gray-600 text-xs rounded-lg hover:bg-gray-200 transition"
                      title="Owner Panel"
                    >
                      Panel
                    </a>
                    <button
                      onClick={() => handleDelete(site.id, site.business_name || "this site")}
                      className="px-3 py-2 bg-red-50 text-red-600 text-xs rounded-lg hover:bg-red-100 transition"
                    >
                      Del
                    </button>
                  </div>

                  <p className="text-xs text-gray-400 mt-2">
                    Created {new Date(site.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
