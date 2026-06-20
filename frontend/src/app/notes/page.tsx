"use client";

const API_BASE = "https://ai-agency-platform.onrender.com";

import { useEffect, useState } from "react";
import { Users, Globe, Mail, Zap, TrendingUp, BarChart3, Bot, LayoutGrid, Settings, ChevronLeft, StickyNote, Trash2, Edit3, MessageCircle, Send, X } from "lucide-react";

interface Note {
  id: string;
  note: string;
  created_at: string;
  replies?: string[];
}

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [replyingId, setReplyingId] = useState<string | null>(null);
  const [replyText, setReplyText] = useState("");

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
    } catch (err) { console.error(err); }
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
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  };

  const deleteNote = async (id: string) => {
    if (!confirm("Delete this note?")) return;
    try {
      await fetch(`${API_BASE}/api/admin/notes/${id}`, { method: "DELETE" });
      loadNotes();
    } catch (err) { console.error(err); }
  };

  const startEdit = (note: Note) => {
    setEditingId(note.id);
    setEditText(note.note.replace("[DONE] ", ""));
  };

  const saveEdit = async () => {
    if (!editingId || !editText.trim()) return;
    try {
      await fetch(`${API_BASE}/api/admin/notes/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: editText.trim() }),
      });
      setEditingId(null);
      setEditText("");
      loadNotes();
    } catch (err) { console.error(err); }
  };

  const toggleNote = async (note: Note) => {
    const isDone = note.note.startsWith("[DONE] ");
    const newText = isDone ? note.note.replace("[DONE] ", "") : "[DONE] " + note.note;
    try {
      await fetch(`${API_BASE}/api/admin/notes/${note.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: newText }),
      });
      loadNotes();
    } catch (err) { console.error(err); }
  };

  const addReply = async (noteId: string) => {
    if (!replyText.trim()) return;
    const note = notes.find(n => n.id === noteId);
    if (!note) return;
    const replies = note.replies || [];
    const timestamp = new Date().toLocaleString();
    const updatedNote = note.note + "\n--- Reply (" + timestamp + ") ---\n" + replyText.trim();
    try {
      await fetch(`${API_BASE}/api/admin/notes/${noteId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: updatedNote }),
      });
      setReplyingId(null);
      setReplyText("");
      loadNotes();
    } catch (err) { console.error(err); }
  };

  useEffect(() => { loadNotes(); }, []);

  const parseNoteAndReplies = (noteText: string) => {
    const parts = noteText.split("\n--- Reply");
    const mainNote = parts[0].replace("[DONE] ", "");
    const replies = parts.slice(1).map(r => r.replace(/^\s*\(.*?\)\s*---\n?/, "").trim());
    return { mainNote, replies, isDone: noteText.startsWith("[DONE] ") };
  };

  return (
    <div className="flex min-h-screen bg-[#020817]">
      {/* Sidebar */}
      <aside className={`${collapsed ? "w-16" : "w-56"} bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col transition-all duration-200 fixed h-full z-20`}>
        <div className="p-4 flex items-center gap-2 border-b border-white/10">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Bot className="w-5 h-5 text-white" />
          </div>
          {!collapsed && <span className="font-bold text-sm text-white">City Maps</span>}
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
        <header className="bg-[#0f172a]/80 backdrop-blur-lg border-b border-white/5 px-6 py-3 sticky top-0 z-10">
          <h1 className="text-xl font-bold text-white">Notes & Conversations</h1>
          <p className="text-xs text-slate-400">Notes, tasks, and team conversations</p>
        </header>

        <div className="p-6 max-w-3xl">
          {/* Add Note */}
          <div className="glass-card-solid p-5 mb-6">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Write a note, task, or start a conversation..."
              rows={3}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-400/30 resize-none mb-3"
              onKeyDown={(e) => { if (e.key === "Enter" && e.ctrlKey) saveNote(); }}
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Ctrl+Enter to save</span>
              <button
                onClick={saveNote}
                disabled={saving || !text.trim()}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:shadow-lg hover:shadow-purple-500/20 transition"
              >
                {saving ? "Saving..." : "Save Note"}
              </button>
            </div>
          </div>

          {/* Notes List */}
          <div className="space-y-3">
            {notes.length === 0 && (
              <p className="text-center text-slate-500 text-sm py-8">No notes yet. Write your first note above.</p>
            )}
            {notes.map((note) => {
              const { mainNote, replies, isDone } = parseNoteAndReplies(note.note);
              return (
              <div key={note.id} className="glass-card-solid p-4 group hover:border-purple-500/20 transition">
                {editingId === note.id ? (
                  <div>
                    <textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={3}
                      className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-400/30 resize-none mb-2" />
                    <div className="flex gap-2">
                      <button onClick={saveEdit} className="px-3 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium">Save</button>
                      <button onClick={() => setEditingId(null)} className="px-3 py-1.5 bg-white/5 text-slate-400 rounded-lg text-xs border border-white/10">Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-2 flex-1">
                        <input type="checkbox" checked={isDone} onChange={() => toggleNote(note)}
                          className="mt-1 w-4 h-4 accent-purple-600 cursor-pointer flex-shrink-0" />
                        <p className={`text-sm whitespace-pre-wrap ${isDone ? "text-slate-500 line-through" : "text-slate-200"}`}>{mainNote}</p>
                      </div>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition">
                        <button onClick={() => startEdit(note)} className="p-1.5 text-slate-400 hover:text-purple-400 hover:bg-purple-500/10 rounded-lg transition">
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => setReplyingId(replyingId === note.id ? null : note.id)} className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition">
                          <MessageCircle className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => deleteNote(note.id)} className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Replies */}
                    {replies.length > 0 && (
                      <div className="mt-3 ml-6 space-y-2 border-l-2 border-purple-500/20 pl-3">
                        {replies.map((reply, i) => (
                          <p key={i} className="text-xs text-slate-400">{reply}</p>
                        ))}
                      </div>
                    )}

                    {/* Reply input */}
                    {replyingId === note.id && (
                      <div className="mt-3 ml-6 flex gap-2">
                        <input value={replyText} onChange={(e) => setReplyText(e.target.value)}
                          placeholder="Write a reply..."
                          className="flex-1 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-purple-400/30"
                          onKeyDown={(e) => { if (e.key === "Enter") addReply(note.id); }}
                        />
                        <button onClick={() => addReply(note.id)} className="p-1.5 bg-purple-600 rounded-lg text-white hover:bg-purple-700 transition">
                          <Send className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}

                    <p className="text-xs text-slate-600 mt-2">{new Date(note.created_at).toLocaleString()}</p>
                  </>
                )}
              </div>
            );})}
          </div>
        </div>
      </main>
    </div>
  );
}
