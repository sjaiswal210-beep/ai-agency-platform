"use client";
const API_BASE = "https://ai-agency-platform.onrender.com";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Receipt, Plus, ArrowLeft, IndianRupee, TrendingUp, Clock, X, FileText, Download } from "lucide-react";

interface Invoice {
  id: string;
  invoice_number: string;
  type: string;
  status: string;
  total: number;
  paid_amount: number;
  currency: string;
  items: any[];
  contact_id: string;
  due_date: string;
  created_at: string;
  crm_contacts?: { name: string; phone: string; email: string };
}

interface DashboardData {
  total_revenue: number;
  total_expenses: number;
  net_income: number;
  total_pending: number;
  invoice_count: number;
  quotation_count: number;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  sent: "bg-blue-100 text-blue-700",
  paid: "bg-green-100 text-green-700",
  overdue: "bg-red-100 text-red-700",
  partially_paid: "bg-amber-100 text-amber-700",
  cancelled: "bg-gray-100 text-gray-500",
};

export default function BillingPage() {
  const params = useParams();
  const orgSlug = params.orgSlug as string;
  const [orgId, setOrgId] = useState("");
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, setFilterType] = useState("");
  const [loading, setLoading] = useState(true);

  // Invoice form
  const [invType, setInvType] = useState("invoice");
  const [customerName, setCustomerName] = useState("");
  const [items, setItems] = useState([{ name: "", quantity: 1, price: 0 }]);
  const [notes, setNotes] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/organizations?search=${orgSlug}`)
      .then(r => r.json())
      .then(d => {
        const found = d.organizations?.find((o: any) => o.slug === orgSlug);
        if (found) { setOrgId(found.id); loadData(found.id); }
      });
  }, [orgSlug]);

  const loadData = (oid?: string) => {
    const id = oid || orgId;
    if (!id) return;
    setLoading(true);
    let url = `${API_BASE}/api/org/${id}/billing/invoices?limit=100`;
    if (filterStatus) url += `&status=${filterStatus}`;
    if (filterType) url += `&type=${filterType}`;
    fetch(url).then(r => r.json()).then(d => { setInvoices(d.invoices || []); setLoading(false); });
    fetch(`${API_BASE}/api/org/${id}/billing/dashboard`).then(r => r.json()).then(setDashboard);
  };

  useEffect(() => { if (orgId) loadData(); }, [filterStatus, filterType]);

  const addItem = () => setItems([...items, { name: "", quantity: 1, price: 0 }]);
  const removeItem = (i: number) => setItems(items.filter((_, idx) => idx !== i));
  const updateItem = (i: number, field: string, value: any) => {
    const updated = [...items];
    (updated[i] as any)[field] = value;
    setItems(updated);
  };

  const subtotal = items.reduce((sum, item) => sum + (item.quantity * item.price), 0);

  const createInvoice = async () => {
    if (items.filter(i => i.name && i.price).length === 0) return;
    setCreating(true);
    try {
      await fetch(`${API_BASE}/api/org/${orgId}/billing/invoices`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: invType,
          items: items.filter(i => i.name),
          notes,
          due_date: dueDate || undefined,
        }),
      });
      setShowCreate(false);
      setItems([{ name: "", quantity: 1, price: 0 }]);
      setNotes(""); setDueDate(""); setCustomerName("");
      loadData();
    } catch (e) { console.error(e); }
    finally { setCreating(false); }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href={`/dashboard/${orgSlug}`} className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <Receipt className="w-6 h-6 text-indigo-600" />
            <div>
              <h1 className="text-lg font-bold">Billing</h1>
              <p className="text-xs text-gray-500">{invoices.length} documents</p>
            </div>
          </div>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700">
            <Plus className="w-3.5 h-3.5" /> New Invoice
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4">
        {/* Stats */}
        {dashboard && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center"><IndianRupee className="w-4 h-4 text-green-600" /></div>
                <span className="text-xs text-gray-500">Revenue</span>
              </div>
              <p className="text-lg font-bold text-gray-900">₹{dashboard.total_revenue.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center"><TrendingUp className="w-4 h-4 text-red-600" /></div>
                <span className="text-xs text-gray-500">Expenses</span>
              </div>
              <p className="text-lg font-bold text-gray-900">₹{dashboard.total_expenses.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center"><Clock className="w-4 h-4 text-amber-600" /></div>
                <span className="text-xs text-gray-500">Pending</span>
              </div>
              <p className="text-lg font-bold text-gray-900">₹{dashboard.total_pending.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center"><FileText className="w-4 h-4 text-indigo-600" /></div>
                <span className="text-xs text-gray-500">Net Income</span>
              </div>
              <p className="text-lg font-bold text-gray-900">₹{dashboard.net_income.toLocaleString()}</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-2 mb-4">
          <select value={filterType} onChange={e => setFilterType(e.target.value)} className="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white">
            <option value="">All Types</option>
            <option value="invoice">Invoices</option>
            <option value="quotation">Quotations</option>
          </select>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white">
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="sent">Sent</option>
            <option value="paid">Paid</option>
            <option value="overdue">Overdue</option>
            <option value="partially_paid">Partially Paid</option>
          </select>
        </div>

        {/* Invoice List */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <p className="text-center text-sm text-gray-400 py-8">Loading...</p>
          ) : invoices.length === 0 ? (
            <div className="text-center py-12">
              <Receipt className="w-10 h-10 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No invoices yet</p>
              <button onClick={() => setShowCreate(true)} className="mt-2 text-xs text-indigo-600 hover:underline">Create your first invoice</button>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500">Number</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500">Customer</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500">Type</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500">Status</th>
                  <th className="text-right px-4 py-2.5 text-xs font-medium text-gray-500">Amount</th>
                  <th className="text-right px-4 py-2.5 text-xs font-medium text-gray-500">Date</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map(inv => (
                  <tr key={inv.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{inv.invoice_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{inv.crm_contacts?.name || "-"}</td>
                    <td className="px-4 py-3"><span className="text-xs capitalize">{inv.type}</span></td>
                    <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[inv.status]}`}>{inv.status.replace("_", " ")}</span></td>
                    <td className="px-4 py-3 text-sm font-medium text-right">₹{Number(inv.total).toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs text-gray-500 text-right">{new Date(inv.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Create Invoice Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Create {invType === "invoice" ? "Invoice" : "Quotation"}</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>

            <div className="space-y-4">
              {/* Type toggle */}
              <div className="flex gap-2">
                <button onClick={() => setInvType("invoice")} className={`flex-1 py-2 rounded-lg text-sm font-medium border transition ${invType === "invoice" ? "bg-indigo-100 border-indigo-300 text-indigo-700" : "border-gray-200"}`}>Invoice</button>
                <button onClick={() => setInvType("quotation")} className={`flex-1 py-2 rounded-lg text-sm font-medium border transition ${invType === "quotation" ? "bg-indigo-100 border-indigo-300 text-indigo-700" : "border-gray-200"}`}>Quotation</button>
              </div>

              {/* Line items */}
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-2">Line Items</label>
                {items.map((item, i) => (
                  <div key={i} className="flex gap-2 mb-2 items-center">
                    <input type="text" value={item.name} onChange={e => updateItem(i, "name", e.target.value)} placeholder="Item name"
                      className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
                    <input type="number" value={item.quantity} onChange={e => updateItem(i, "quantity", parseInt(e.target.value) || 1)} min="1"
                      className="w-16 px-2 py-2 border border-gray-200 rounded-lg text-sm text-center" />
                    <input type="number" value={item.price} onChange={e => updateItem(i, "price", parseFloat(e.target.value) || 0)} placeholder="Price"
                      className="w-24 px-2 py-2 border border-gray-200 rounded-lg text-sm text-right" />
                    {items.length > 1 && (
                      <button onClick={() => removeItem(i)} className="text-red-400 hover:text-red-600 text-sm">✕</button>
                    )}
                  </div>
                ))}
                <button onClick={addItem} className="text-xs text-indigo-600 hover:underline mt-1">+ Add line item</button>
              </div>

              {/* Subtotal */}
              <div className="bg-gray-50 rounded-lg p-3 flex justify-between items-center">
                <span className="text-sm text-gray-600">Subtotal</span>
                <span className="text-lg font-bold text-gray-900">₹{subtotal.toLocaleString()}</span>
              </div>

              {/* Due date and Notes */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Due Date</label>
                  <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Notes</label>
                  <input type="text" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Thank you for your business"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                </div>
              </div>

              <button onClick={createInvoice} disabled={creating || items.filter(i => i.name && i.price).length === 0}
                className="w-full py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
                {creating ? "Creating..." : `Create ${invType === "invoice" ? "Invoice" : "Quotation"}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}