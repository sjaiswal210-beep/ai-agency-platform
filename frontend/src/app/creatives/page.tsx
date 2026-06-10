"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";
import { useEffect, useState } from "react";
import { api, Website } from "@/lib/api";
import { Bot, ArrowLeft, Image, RefreshCw } from "lucide-react";

const TEMPLATES = [
  { id: "offer", name: "Special Offer", icon: "🎉" },
  { id: "testimonial", name: "Customer Review", icon: "⭐" },
  { id: "announcement", name: "Announcement", icon: "📢" },
  { id: "tips", name: "Tips & Education", icon: "💡" },
  { id: "festival", name: "Festival Greeting", icon: "🪔" },
  { id: "before_after", name: "Before & After", icon: "✨" },
  { id: "hiring", name: "We are Hiring", icon: "👥" },
  { id: "milestone", name: "Milestone", icon: "🏆" },
];

const PLATFORMS = [
  { id: "instagram", name: "Instagram (1080x1080)" },
  { id: "facebook", name: "Facebook (1200x630)" },
  { id: "whatsapp", name: "WhatsApp (800x800)" },
  { id: "story", name: "Story (1080x1920)" },
];

export default function CreativesPage() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selected, setSelected] = useState("");
  const [template, setTemplate] = useState("offer");
  const [platform, setPlatform] = useState("instagram");
  const [customText, setCustomText] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { api.websites.list().then(setWebsites).catch(console.error); }, []);

  const generate = () => {
    if (!selected) return;
    setLoading(true);
    const url = `${API_BASE}/api/creatives/${selected}/generate?type=${template}&platform=${platform}&custom_text=${encodeURIComponent(customText)}`;
    setPreviewUrl(url + "&t=" + Date.now());
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 px-6 py-3 sticky top-0 z-10">
        <div className="flex items-center gap-3 max-w-7xl mx-auto">
          <a href="/" className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
          <Bot className="w-7 h-7 text-primary" />
          <h1 className="text-lg font-bold">Ad Creatives</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ minHeight: "calc(100vh - 120px)" }}>
          {/* Controls */}
          <div className="space-y-4">
            <select value={selected} onChange={(e) => setSelected(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
              <option value="">Select website...</option>
              {websites.map((w) => <option key={w.id} value={w.id}>{w.template} - {w.id.slice(0, 8)}</option>)}
            </select>

            <div className="bg-white rounded-xl border border-gray-100 p-4">
              <p className="text-xs font-medium text-gray-500 mb-2">Template</p>
              <div className="grid grid-cols-2 gap-2">
                {TEMPLATES.map((t) => (
                  <button key={t.id} onClick={() => setTemplate(t.id)}
                    className={`p-2 rounded-lg text-xs text-left transition ${template === t.id ? "bg-primary/10 border border-primary/30" : "bg-gray-50 border border-transparent hover:border-gray-200"}`}>
                    <span className="text-lg">{t.icon}</span>
                    <p className="mt-1 font-medium">{t.name}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-100 p-4">
              <p className="text-xs font-medium text-gray-500 mb-2">Platform</p>
              <div className="space-y-1">
                {PLATFORMS.map((p) => (
                  <button key={p.id} onClick={() => setPlatform(p.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs transition ${platform === p.id ? "bg-primary/10 text-primary font-medium" : "text-gray-600 hover:bg-gray-50"}`}>
                    {p.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-100 p-4">
              <p className="text-xs font-medium text-gray-500 mb-2">Custom Text (optional)</p>
              <input type="text" value={customText} onChange={(e) => setCustomText(e.target.value)}
                placeholder="e.g., 20% off this week, Diwali special..."
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
            </div>

            <button onClick={generate} disabled={!selected || loading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl text-sm font-medium disabled:opacity-50 hover:shadow-lg hover:shadow-indigo-500/25 transition-all">
              {loading ? <><RefreshCw className="w-4 h-4 animate-spin" /> Generating...</> : <><Image className="w-4 h-4" /> Generate Creative</>}
            </button>
          </div>

          {/* Preview */}
          <div className="lg:col-span-2 bg-gray-900 rounded-xl overflow-hidden flex items-center justify-center min-h-[500px]">
            {previewUrl ? (
              <iframe src={previewUrl} className="w-full h-full border-0 min-h-[600px]" title="Creative Preview" />
            ) : (
              <div className="text-center text-gray-500">
                <Image className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a website and template to generate</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
