"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

import { useEffect, useState } from "react";
import { api, Website } from "@/lib/api";
import { Bot, ArrowLeft, Send, RefreshCw, ExternalLink, Palette, Image, MessageSquare, Sparkles } from "lucide-react";

type Tab = "edit" | "theme" | "logo" | "social" | "video";

interface ThemeOption {
  id: string;
  name: string;
  description: string;
  colors: { primary: string; secondary: string; accent: string; background: string; text: string };
  style: string;
}

const THEMES: ThemeOption[] = [
  { id: "modern-dark", name: "Modern Dark", description: "Sleek dark UI with vibrant accents", colors: { primary: "#6366f1", secondary: "#1e1b4b", accent: "#818cf8", background: "#0f172a", text: "#f8fafc" }, style: "modern" },
  { id: "clean-light", name: "Clean Light", description: "Bright, minimal, and professional", colors: { primary: "#2563eb", secondary: "#eff6ff", accent: "#3b82f6", background: "#ffffff", text: "#1e293b" }, style: "minimal" },
  { id: "bold-vibrant", name: "Bold & Vibrant", description: "Eye-catching colors with strong contrast", colors: { primary: "#dc2626", secondary: "#fef2f2", accent: "#f97316", background: "#ffffff", text: "#111827" }, style: "bold" },
  { id: "elegant-gold", name: "Elegant Gold", description: "Luxury feel with gold accents", colors: { primary: "#b45309", secondary: "#1c1917", accent: "#d97706", background: "#0c0a09", text: "#fafaf9" }, style: "elegant" },
  { id: "nature-green", name: "Nature Green", description: "Fresh and organic feel", colors: { primary: "#16a34a", secondary: "#f0fdf4", accent: "#22c55e", background: "#ffffff", text: "#14532d" }, style: "modern" },
  { id: "ocean-blue", name: "Ocean Blue", description: "Calm and trustworthy", colors: { primary: "#0891b2", secondary: "#ecfeff", accent: "#06b6d4", background: "#ffffff", text: "#164e63" }, style: "minimal" },
  { id: "sunset-warm", name: "Sunset Warm", description: "Warm gradient tones", colors: { primary: "#e11d48", secondary: "#fff1f2", accent: "#f43f5e", background: "#ffffff", text: "#1f2937" }, style: "playful" },
  { id: "purple-haze", name: "Purple Haze", description: "Creative and modern purple theme", colors: { primary: "#7c3aed", secondary: "#faf5ff", accent: "#a78bfa", background: "#ffffff", text: "#1e1b4b" }, style: "modern" },
  { id: "midnight", name: "Midnight", description: "Deep dark with cool blue tones", colors: { primary: "#3b82f6", secondary: "#172554", accent: "#60a5fa", background: "#020617", text: "#e2e8f0" }, style: "modern" },
];

export default function EditorPage() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [tab, setTab] = useState<Tab>("edit");
  const [logoStyle, setLogoStyle] = useState("modern");
  const [socialPlatform, setSocialPlatform] = useState("instagram");
  const [socialPurpose, setSocialPurpose] = useState("promotion");
  const [previewUrl, setPreviewUrl] = useState("");
  const [videoPrompt, setVideoPrompt] = useState("");
  const [videoIdea, setVideoIdea] = useState("");
  const [showIdeaInput, setShowIdeaInput] = useState(false);
  const [generatingPrompt, setGeneratingPrompt] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoClips, setVideoClips] = useState<any[]>([]);
  const [numClips, setNumClips] = useState(3);
  const [selectedTheme, setSelectedTheme] = useState<string>("");

  useEffect(() => {
    api.websites.list().then(setWebsites).catch(console.error);
  }, []);

  useEffect(() => {
    if (selected) {
      setPreviewUrl(`${API_BASE}/api/preview/${selected}`);
    }
  }, [selected, refreshKey]);

  const handleEdit = async () => {
    if (!selected || !prompt.trim()) return;
    setLoading(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/api/editor/${selected}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });
      if (res.ok) {
        setMessage("Website updated!");
        setRefreshKey((k) => k + 1);
        setPrompt("");
      } else {
        const err = await res.json();
        setMessage(`Error: ${err.detail || "Failed"}`);
      }
    } catch (e: any) { setMessage(e?.name === "AbortError" ? "Error: Video generation timed out (>3min). Try fewer clips." : "Error: Server unreachable. Try again."); }
    finally { setLoading(false); }
  };

  const handleThemeApply = async (theme: ThemeOption) => {
    if (!selected) return;
    setLoading(true);
    setMessage("");
    setSelectedTheme(theme.id);
    try {
      const themePrompt = `Change the website theme to "${theme.name}" style. Update the color_scheme to use these colors: primary color ${theme.colors.primary}, secondary color ${theme.colors.secondary}, accent color ${theme.colors.accent}, background color ${theme.colors.background}, text color ${theme.colors.text}. The overall style should be ${theme.style} and ${theme.description.toLowerCase()}.`;
      const res = await fetch(`${API_BASE}/api/editor/${selected}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: themePrompt }),
      });
      if (res.ok) {
        setMessage(`Theme "${theme.name}" applied!`);
        setRefreshKey((k) => k + 1);
      } else {
        const err = await res.json();
        setMessage(`Error: ${err.detail || "Failed to apply theme"}`);
      }
    } catch (e: any) { setMessage("Error: Server unreachable. Try again."); }
    finally { setLoading(false); }
  };

  const handleLogo = async () => {
    if (!selected) return;
    setLoading(true);
    setPreviewUrl(`${API_BASE}/api/branding/${selected}/logo/preview?style=${logoStyle}&t=${Date.now()}`);
    setLoading(false);
    setMessage("Logo generated! See preview.");
  };

  const handleVideo = async () => {
    if (!selected) return;
    setVideoLoading(true);
    setVideoUrl("");
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/api/video/${selected}/generate-long`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: videoPrompt, clips: numClips }),
      });
      const data = await res.json();
      if (data.clips && data.clips.length > 0) {
        setVideoClips(data.clips);
        setVideoUrl(data.combined_url || data.clips[0]?.url || "");
        setMessage(data.combined_url ? `${data.total_duration} video stitched and ready!` : `${data.total_duration} video generated (${data.clips.length} clips)!`);
      } else {
        setMessage("Error: " + (data.detail || "Failed to generate"));
      }
    } catch (e: any) { setMessage(e?.name === "AbortError" ? "Error: Video generation timed out (>3min). Try fewer clips." : "Error: Server unreachable. Try again."); }
    finally { setVideoLoading(false); }
  };

  const generateDetailedPrompt = async () => {
    if (!selected || !videoIdea.trim()) return;
    setGeneratingPrompt(true);
    try {
      const res = await fetch(`${API_BASE}/api/video/${selected}/detailed-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: videoIdea }),
      });
      const data = await res.json();
      setVideoPrompt(data.prompt || "");
      setShowIdeaInput(false);
    } catch { setMessage("Error generating prompt"); }
    finally { setGeneratingPrompt(false); }
  };

  const handleSocial = async () => {
    if (!selected) return;
    setLoading(true);
    setPreviewUrl(`${API_BASE}/api/branding/${selected}/social-post/preview?platform=${socialPlatform}&purpose=${socialPurpose}&t=${Date.now()}`);
    setLoading(false);
    setMessage("Social post generated! See preview.");
  };

  return (
    <div className="min-h-screen bg-[#020817]">
      <header className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] border-b border-white/10 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-slate-400 hover:text-slate-300"><ArrowLeft className="w-5 h-5" /></a>
            <Bot className="w-7 h-7 text-primary" />
            <h1 className="text-lg font-bold text-white">Website Editor</h1>
          </div>
          <div className="flex items-center gap-2">
            {selected && (
              <a href={`${API_BASE}/api/preview/${selected}`} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 px-3 py-1.5 bg-primary text-white rounded-lg text-xs hover:bg-primary-dark">
                <ExternalLink className="w-3 h-3" /> Full Preview
              </a>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ height: "calc(100vh - 100px)" }}>
          {/* Left panel */}
          <div className="flex flex-col gap-3">
            {/* Website selector */}
            <select value={selected} onChange={(e) => { setSelected(e.target.value); setRefreshKey((k) => k + 1); setPreviewUrl(`${API_BASE}/api/preview/${e.target.value}`); }}
              className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm bg-white/[0.03]">
              <option value="">Select website...</option>
              {websites.map((w) => (
                <option key={w.id} value={w.id}>{w.template} - {w.id.slice(0, 8)}...</option>
              ))}
            </select>

            {/* Tabs */}
            <div className="flex gap-1 bg-white/5 p-1 rounded-lg">
              <button onClick={() => { setTab("edit"); if(selected) setPreviewUrl(`${API_BASE}/api/preview/${selected}`); }}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "edit" ? "bg-white shadow text-primary" : "text-slate-300"}`}>
                <Send className="w-3 h-3" /> Edit
              </button>
              <button onClick={() => setTab("theme")}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "theme" ? "bg-white shadow text-primary" : "text-slate-300"}`}>
                <Sparkles className="w-3 h-3" /> Theme
              </button>
              <button onClick={() => setTab("logo")}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "logo" ? "bg-white shadow text-primary" : "text-slate-300"}`}>
                <Palette className="w-3 h-3" /> Logo
              </button>
              <button onClick={() => setTab("social")}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "social" ? "bg-white shadow text-primary" : "text-slate-300"}`}>
                <Image className="w-3 h-3" /> Social
              </button>
              <button onClick={() => setTab("video")}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "video" ? "bg-white shadow text-primary" : "text-slate-300"}`}>
                &#127909; Video
              </button>
            </div>

            {/* Tab content */}
            <div className="bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl shadow-lg shadow-black/10 border border-white/5 p-4 flex-1 flex flex-col overflow-hidden">
              {tab === "edit" && (
                <>
                  <label className="text-xs font-medium text-slate-300 mb-1">What do you want to change?</label>
                  <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Examples:&#10;- Change color to dark blue&#10;- Add a new service&#10;- Update business hours&#10;- Make headline more catchy&#10;- Add FAQ about pricing"
                    className="flex-1 w-full px-3 py-2 border border-white/10 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50" />
                  <button onClick={handleEdit} disabled={loading || !selected || !prompt.trim()}
                    className="mt-2 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark transition">
                    {loading ? <><RefreshCw className="w-3 h-3 animate-spin" /> Updating...</> : <><Send className="w-3 h-3" /> Apply Changes</>}
                  </button>
                </>
              )}

              {tab === "theme" && (
                <>
                  <label className="text-xs font-medium text-slate-300 mb-2">Choose a Theme</label>
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                    {THEMES.map((theme) => (
                      <button
                        key={theme.id}
                        onClick={() => handleThemeApply(theme)}
                        disabled={loading || !selected}
                        className={`w-full text-left p-3 rounded-lg border transition hover:border-primary/50 disabled:opacity-50 ${
                          selectedTheme === theme.id ? "border-primary bg-primary/10" : "border-white/10 bg-white/[0.02]"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {/* Color preview dots */}
                          <div className="flex gap-1 shrink-0">
                            <div className="w-4 h-4 rounded-full border border-white/20" style={{ background: theme.colors.primary }} />
                            <div className="w-4 h-4 rounded-full border border-white/20" style={{ background: theme.colors.accent }} />
                            <div className="w-4 h-4 rounded-full border border-white/20" style={{ background: theme.colors.background }} />
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-white truncate">{theme.name}</p>
                            <p className="text-xs text-slate-400 truncate">{theme.description}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                  {loading && (
                    <div className="mt-2 flex items-center justify-center gap-2 text-xs text-slate-300">
                      <RefreshCw className="w-3 h-3 animate-spin" /> Applying theme...
                    </div>
                  )}
                </>
              )}

              {tab === "logo" && (
                <>
                  <label className="text-xs font-medium text-slate-300 mb-2">Logo Style</label>
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {["modern", "minimal", "bold", "elegant", "playful"].map((s) => (
                      <button key={s} onClick={() => setLogoStyle(s)}
                        className={`px-3 py-2 rounded-lg text-xs font-medium capitalize transition ${logoStyle === s ? "bg-primary text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
                        {s}
                      </button>
                    ))}
                  </div>
                  <button onClick={handleLogo} disabled={!selected}
                    className="mt-auto w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark transition">
                    <Palette className="w-3 h-3" /> Generate Logo
                  </button>
                </>
              )}

              {tab === "video" && (
                <>
                  {!showIdeaInput && !videoPrompt && (
                    <div className="flex-1 flex flex-col items-center justify-center gap-3">
                      <p className="text-sm text-slate-300 text-center">What kind of video do you want?</p>
                      <button onClick={() => setShowIdeaInput(true)}
                        className="px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20">
                        Describe your idea
                      </button>
                    </div>
                  )}

                  {showIdeaInput && !videoPrompt && (
                    <div className="flex-1 flex flex-col">
                      <label className="text-xs font-medium text-slate-300 mb-1">Your Video Idea</label>
                      <textarea value={videoIdea} onChange={(e) => setVideoIdea(e.target.value)}
                        placeholder="Describe your idea briefly...&#10;&#10;Examples:&#10;- Show the gym equipment and people exercising&#10;- A chef cooking in the kitchen&#10;- Happy customers at the salon&#10;- Before/after dental treatment&#10;- Hotel room tour with amenities"
                        className="flex-1 w-full px-3 py-2 border border-white/10 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50" />
                      <button onClick={generateDetailedPrompt} disabled={generatingPrompt || !videoIdea.trim()}
                        className="mt-2 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark transition">
                        {generatingPrompt ? "Creating detailed prompt..." : "Generate Video Script"}
                      </button>
                    </div>
                  )}

                  {videoPrompt && (
                    <div className="flex-1 flex flex-col">
                      <label className="text-xs font-medium text-slate-300 mb-1">AI-Generated Video Prompt</label>
                      <textarea value={videoPrompt} onChange={(e) => setVideoPrompt(e.target.value)}
                        className="flex-1 w-full px-3 py-2 border border-white/10 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50" />
                      <div className="flex gap-2 mt-2 mb-2">
                        <label className="text-xs text-slate-300 self-center">Clips:</label>
                        {[2, 3, 4, 5].map((n) => (
                          <button key={n} onClick={() => setNumClips(n)}
                            className={`px-2 py-1 rounded text-xs font-medium ${numClips === n ? "bg-primary text-white" : "bg-white/5 text-slate-300"}`}>
                            {n}x10s
                          </button>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <button onClick={handleVideo} disabled={videoLoading || !selected}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark transition">
                          {videoLoading ? `Generating ${numClips} clips...` : `Generate ${numClips * 10}s Video`}
                        </button>
                        <button onClick={() => { setVideoPrompt(""); setVideoIdea(""); setShowIdeaInput(false); }}
                          className="px-3 py-2.5 bg-white/5 text-slate-300 rounded-lg text-sm hover:bg-white/10">
                          Reset
                        </button>
                      </div>
                      {videoClips.length > 0 && (
                        <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                          {videoClips.map((clip: any) => (
                            <a key={clip.scene} href={clip.url} target="_blank" rel="noopener noreferrer"
                              className="flex items-center justify-between px-3 py-1.5 bg-green-50 text-green-600 rounded-lg text-xs hover:bg-green-100">
                              <span>Clip {clip.scene}</span>
                              <span>Download</span>
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {tab === "social" && (
                <>
                  <label className="text-xs font-medium text-slate-300 mb-1">Platform</label>
                  <select value={socialPlatform} onChange={(e) => setSocialPlatform(e.target.value)}
                    className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm mb-3">
                    <option value="instagram">Instagram Post</option>
                    <option value="facebook">Facebook Post</option>
                    <option value="whatsapp_status">WhatsApp Status</option>
                  </select>
                  <label className="text-xs font-medium text-slate-300 mb-1">Purpose</label>
                  <select value={socialPurpose} onChange={(e) => setSocialPurpose(e.target.value)}
                    className="w-full px-3 py-2 border border-white/10 rounded-lg text-sm mb-3">
                    <option value="promotion">Promotion</option>
                    <option value="offer">Special Offer</option>
                    <option value="announcement">Announcement</option>
                    <option value="testimonial">Customer Testimonial</option>
                  </select>
                  <button onClick={handleSocial} disabled={!selected}
                    className="mt-auto w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark transition">
                    <Image className="w-3 h-3" /> Generate Post
                  </button>
                </>
              )}

              {message && (
                <p className={`mt-2 text-xs ${message.includes("Error") ? "text-red-500" : "text-green-600"}`}>{message}</p>
              )}
            </div>
          </div>

          {/* Right: Preview */}
          <div className="lg:col-span-2 bg-white/[0.03] backdrop-blur-xl border-white/[0.06] rounded-xl shadow-lg shadow-black/10 border border-white/5 overflow-hidden">
            {selected && previewUrl ? (
              <iframe key={refreshKey + previewUrl} src={previewUrl} className="w-full h-full border-0" title="Preview" />
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400 text-sm">Select a website to start editing</div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
