"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

import { useEffect, useState } from "react";
import { Users, Globe, Mail, Zap, TrendingUp, BarChart3, Bot, LayoutGrid, Settings, ChevronLeft, StickyNote, Trash2 } from "lucide-react";

interface Note {
  id: string;
  note: string;
  created_at: string;
}

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { name: "Dashboard", icon: LayoutGrid, href: "/" },
    { name: "Leads", icon: Users, href: "/leads" },
    { name: "Websites", icon: Globe, href: "/websites" },
    { name: "Outreach", icon: Mail, href: "/outreach" },
    { name: "Editor", icon: Zap, href: "/editor" },
    { name: "Tools", icon: Bot, href: "/tools" },
    { name: "Creatives", icon: Zap, href: "/creatives" },
    { name: "Growth", icon: TrendingUp, href: "/growth" },
    { name: "Analytics", icon: BarChart3, href: "/analytics" },
    { name: "Notes", icon: StickyNote, href: "/notes", active: true },
  ];

  const loadNotes = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/notes`);
      const data = await res.json();
      setNotes(data);
    } catch (err) {
      console.error(err);
    }
  };

  const saveNote = async () => {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await fetch(`${API_BASE}/api/admin/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }),
      });
      setText("");
      loadNotes();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const deleteNote = async (id: string) => {
    try {
      await fetch(`${API_BASE}/api/admin/notes/${id}`, { method: "DELETE" });
      loadNotes();
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadNotes();
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`${collapsed ? "w-16" : "w-56"} bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col transition-all duration-200 fixed h-full z-20`}>
        <div className="p-4 flex items-center gap-2 border-b border-white/10">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Bot className="w-5 h-5 text-white" />
          </div>
          {!collapsed && <span className="font-bold text-sm text-white">AI Employee</span>}
        </div>
        <nav className="flex-1 py-3 px-2 space-y-1">
          {navItems.map((item) => (
            <a key={item.name} href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                item.active ? "bg-white/10 text-white font-medium" : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}>
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </a>
          ))}
        </nav>
        <div className="border-t border-white/10 p-2">
          <button onClick={() => setCollapsed(!collapsed)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-500 hover:bg-white/5 hover:text-white w-full">
            <ChevronLeft className={`w-4 h-4 transition ${collapsed ? "rotate-180" : ""}`} />
            {!collapsed && <span>Collapse</span>}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className={`flex-1 ${collapsed ? "ml-16" : "ml-56"} transition-all duration-200`}>
        <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 px-6 py-3 sticky top-0 z-10">
          <h1 className="text-xl font-bold">Notes</h1>
          <p className="text-xs text-gray-500">Save quick notes and reminders</p>
        </header>

        <div className="p-6 max-w-3xl">
          {/* Add Note */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 shadow-sm">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Write a note... (ideas, reminders, tasks)"
              rows={3}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/30 resize-none mb-3"
              onKeyDown={(e) => { if (e.key === "Enter" && e.ctrlKey) saveNote(); }}
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Ctrl+Enter to save</span>
              <button
                onClick={saveNote}
                disabled={saving || !text.trim()}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-purple-700 transition"
              >
                {saving ? "Saving..." : "Save Note"}
              </button>
            </div>
          </div>

          {/* Notes List */}
          <div className="space-y-3">
            {notes.length === 0 && (
              <p className="text-center text-gray-400 text-sm py-8">No notes yet. Write your first note above.</p>
            )}
            {notes.map((note) => (
              <div key={note.id} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm group hover:border-purple-200 transition">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap flex-1">{note.note}</p>
                  <button
                    onClick={() => deleteNote(note.id)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-2">{new Date(note.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
