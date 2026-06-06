"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

import { useEffect, useState } from "react";
import { api, Website } from "@/lib/api";
import { Bot, ArrowLeft, Wrench, Send, Copy, Check } from "lucide-react";

interface Tool {
  id: string;
  name: string;
  icon: string;
  desc: string;
}

export default function ToolsPage() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selected, setSelected] = useState("");
  const [tools, setTools] = useState<Tool[]>([]);
  const [category, setCategory] = useState("");
  const [activeTool, setActiveTool] = useState<Tool | null>(null);
  const [context, setContext] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.websites.list().then(setWebsites).catch(console.error);
  }, []);

  useEffect(() => {
    if (selected) {
      fetch(`${API_BASE}/api/toolkit/${selected}/tools`)
        .then((r) => r.json())
        .then((data) => {
          setTools(data.tools);
          setCategory(data.category);
        })
        .catch(console.error);
    }
  }, [selected]);

  const runTool = async () => {
    if (!selected || !activeTool) return;
    setLoading(true);
    setResult("");
    try {
      const res = await fetch(`${API_BASE}/api/toolkit/${selected}/tools/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool_id: activeTool.id, context }),
      });
      const data = await res.json();
      setResult(data.content);
    } catch {
      setResult("Error: Could not generate content");
    } finally {
      setLoading(false);
    }
  };

  const copyResult = () => {
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <Bot className="w-7 h-7 text-primary" />
            <h1 className="text-lg font-bold">Business Toolkit</h1>
            {category && <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full capitalize">{category}</span>}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4">
        {/* Website selector */}
        <select value={selected} onChange={(e) => { setSelected(e.target.value); setActiveTool(null); setResult(""); }}
          className="w-full max-w-md px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white mb-4">
          <option value="">Select a website...</option>
          {websites.map((w) => (
            <option key={w.id} value={w.id}>{w.template} - {w.id.slice(0, 8)}...</option>
          ))}
        </select>

        {tools.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ minHeight: "calc(100vh - 180px)" }}>
            {/* Tools grid */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Available Tools</p>
              {tools.map((tool) => (
                <button key={tool.id} onClick={() => { setActiveTool(tool); setResult(""); }}
                  className={`w-full text-left p-3 rounded-lg border transition ${
                    activeTool?.id === tool.id
                      ? "bg-primary/5 border-primary/30 shadow-sm"
                      : "bg-white border-gray-100 hover:border-gray-200"
                  }`}>
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{tool.icon}</span>
                    <div>
                      <p className="text-sm font-medium">{tool.name}</p>
                      <p className="text-xs text-gray-500">{tool.desc}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Tool runner + result */}
            <div className="lg:col-span-2 flex flex-col gap-4">
              {activeTool ? (
                <>
                  <div className="bg-white rounded-xl border border-gray-100 p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">{activeTool.icon}</span>
                      <div>
                        <h2 className="font-semibold">{activeTool.name}</h2>
                        <p className="text-xs text-gray-500">{activeTool.desc}</p>
                      </div>
                    </div>
                    <textarea value={context} onChange={(e) => setContext(e.target.value)}
                      placeholder="Add extra context (optional)... e.g., 'for Diwali festival' or 'target young professionals' or 'include 20% discount'"
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-primary/50" />
                    <button onClick={runTool} disabled={loading}
                      className="mt-2 flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark transition">
                      {loading ? "Generating..." : <><Wrench className="w-3 h-3" /> Generate Content</>}
                    </button>
                  </div>

                  {result && (
                    <div className="bg-white rounded-xl border border-gray-100 p-4 flex-1 overflow-auto">
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-xs font-medium text-gray-500">Generated Content</p>
                        <button onClick={copyResult}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 rounded hover:bg-gray-200 transition">
                          {copied ? <><Check className="w-3 h-3 text-green-500" /> Copied</> : <><Copy className="w-3 h-3" /> Copy</>}
                        </button>
                      </div>
                      <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm text-gray-700">{result}</div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                  Select a tool from the left to get started
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
