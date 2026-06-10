"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

import { useEffect, useState } from "react";
import { api, Website } from "@/lib/api";
import { Bot, ArrowLeft, Send, RefreshCw, ExternalLink, Palette, Image, MessageSquare } from "lucide-react";

type Tab = "edit" | "logo" | "social" | "video";

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
    } catch { setMessage("Error: Server unreachable"); }
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
    } catch { setMessage("Error: Server unreachable"); }
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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <Bot className="w-7 h-7 text-primary" />
            <h1 className="text-lg font-bold">Website Editor</h1>
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
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
              <option value="">Select website...</option>
              {websites.map((w) => (
                <option key={w.id} value={w.id}>{w.template} - {w.id.slice(0, 8)}...</option>
              ))}
            </select>

            {/* Tabs */}
            <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
              <button onClick={() => { setTab("edit"); if(selected) setPreviewUrl(`${API_BASE}/api/preview/${selected}`); }}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "edit" ? "bg-white shadow text-primary" : "text-gray-500"}`}>
                <Send className="w-3 h-3" /> Edit
              </button>
              <button onClick={() => setTab("logo")}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "logo" ? "bg-white shadow text-primary" : "text-gray-500"}`}>
                <Palette className="w-3 h-3" /> Logo
              </button>
              <button onClick={() => setTab("social")}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "social" ? "bg-white shadow text-primary" : "text-gray-500"}`}>
                <Image className="w-3 h-3" /> Social
              </button>
              <button onClick={() => setTab("video")}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-xs font-medium transition ${tab === "video" ? "bg-white shadow text-primary" : "text-gray-500"}`}>
                &#127909; Video
              </button>
            </div>

            {/* Tab content */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex-1 flex flex-col">
              {tab === "edit" && (
                <>
                  <label className="text-xs font-medium text-gray-500 mb-1">What do you want to change?</label>
                  <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Examples:&#10;- Change color to dark blue&#10;- Add a new service&#10;- Update business hours&#10;- Make headline more catchy&#10;- Add FAQ about pricing"
                    className="flex-1 w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50" />
                  <button onClick={handleEdit} disabled={loading || !selected || !prompt.trim()}
                    className="mt-2 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark transition">
                    {loading ? <><RefreshCw className="w-3 h-3 animate-spin" /> Updating...</> : <><Send className="w-3 h-3" /> Apply Changes</>}
                  </button>
                </>
              )}

              {tab === "logo" && (
                <>
                  <label className="text-xs font-medium text-gray-500 mb-2">Logo Style</label>
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {["modern", "minimal", "bold", "elegant", "playful"].map((s) => (
                      <button key={s} onClick={() => setLogoStyle(s)}
                        className={`px-3 py-2 rounded-lg text-xs font-medium capitalize transition ${logoStyle === s ? "bg-primary text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
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
                      <p className="text-sm text-gray-500 text-center">What kind of video do you want?</p>
                      <button onClick={() => setShowIdeaInput(true)}
                        className="px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20">
                        Describe your idea
                      </button>
                    </div>
                  )}

                  {showIdeaInput && !videoPrompt && (
                    <div className="flex-1 flex flex-col">
                      <label className="text-xs font-medium text-gray-500 mb-1">Your Video Idea</label>
                      <textarea value={videoIdea} onChange={(e) => setVideoIdea(e.target.value)}
                        placeholder="Describe your idea briefly...&#10;&#10;Examples:&#10;- Show the gym equipment and people exercising&#10;- A chef cooking in the kitchen&#10;- Happy customers at the salon&#10;- Before/after dental treatment&#10;- Hotel room tour with amenities"
                        className="flex-1 w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50" />
                      <button onClick={generateDetailedPrompt} disabled={generatingPrompt || !videoIdea.trim()}
                        className="mt-2 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark transition">
                        {generatingPrompt ? "Creating detailed prompt..." : "Generate Video Script"}
                      </button>
                    </div>
                  )}

                  {videoPrompt && (
                    <div className="flex-1 flex flex-col">
                      <label className="text-xs font-medium text-gray-500 mb-1">AI-Generated Video Prompt</label>
                      <textarea value={videoPrompt} onChange={(e) => setVideoPrompt(e.target.value)}
                        className="flex-1 w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50" />
                      <div className="flex gap-2 mt-2 mb-2">
                        <label className="text-xs text-gray-500 self-center">Clips:</label>
                        {[2, 3, 4, 5].map((n) => (
                          <button key={n} onClick={() => setNumClips(n)}
                            className={`px-2 py-1 rounded text-xs font-medium ${numClips === n ? "bg-primary text-white" : "bg-gray-100 text-gray-600"}`}>
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
                          className="px-3 py-2.5 bg-gray-100 text-gray-600 rounded-lg text-sm hover:bg-gray-200">
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
                  <label className="text-xs font-medium text-gray-500 mb-1">Platform</label>
                  <select value={socialPlatform} onChange={(e) => setSocialPlatform(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm mb-3">
                    <option value="instagram">Instagram Post</option>
                    <option value="facebook">Facebook Post</option>
                    <option value="whatsapp_status">WhatsApp Status</option>
                  </select>
                  <label className="text-xs font-medium text-gray-500 mb-1">Purpose</label>
                  <select value={socialPurpose} onChange={(e) => setSocialPurpose(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm mb-3">
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
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            {selected && previewUrl ? (
              <iframe key={refreshKey + previewUrl} src={previewUrl} className="w-full h-full border-0" title="Preview" />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm">Select a website to start editing</div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
