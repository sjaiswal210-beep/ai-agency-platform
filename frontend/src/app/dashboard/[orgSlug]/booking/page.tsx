"use client";
const API_BASE = "https://ai-agency-platform.onrender.com";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Calendar, Plus, ArrowLeft, Clock, User, X, Check, Phone } from "lucide-react";

interface Service {
  id: string;
  name: string;
  duration_minutes: number;
  price: number;
  is_active: boolean;
}

interface Staff {
  id: string;
  name: string;
  phone: string;
  is_active: boolean;
}

interface Appointment {
  id: string;
  customer_name: string;
  customer_phone: string;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
  notes: string;
  source: string;
  booking_services?: { name: string; duration_minutes: number };
  booking_staff?: { name: string };
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  confirmed: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
  no_show: "bg-gray-100 text-gray-600",
};

export default function BookingPage() {
  const params = useParams();
  const orgSlug = params.orgSlug as string;
  const [orgId, setOrgId] = useState("");
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showService, setShowService] = useState(false);
  const [tab, setTab] = useState<"appointments" | "services" | "staff">("appointments");
  const [dateFilter, setDateFilter] = useState(new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState(true);

  // Appointment form
  const [custName, setCustName] = useState("");
  const [custPhone, setCustPhone] = useState("");
  const [apptDate, setApptDate] = useState(new Date().toISOString().split("T")[0]);
  const [apptTime, setApptTime] = useState("10:00");
  const [apptServiceId, setApptServiceId] = useState("");
  const [apptStaffId, setApptStaffId] = useState("");
  const [apptNotes, setApptNotes] = useState("");
  const [creating, setCreating] = useState(false);

  // Service form
  const [svcName, setSvcName] = useState("");
  const [svcDuration, setSvcDuration] = useState(60);
  const [svcPrice, setSvcPrice] = useState(0);

  useEffect(() => {
    fetch(`${API_BASE}/api/organizations?search=${orgSlug}`)
      .then(r => r.json())
      .then(d => {
        const found = d.organizations?.find((o: any) => o.slug === orgSlug);
        if (found) { setOrgId(found.id); loadAll(found.id); }
      });
  }, [orgSlug]);

  const loadAll = (oid?: string) => {
    const id = oid || orgId;
    if (!id) return;
    setLoading(true);
    fetch(`${API_BASE}/api/org/${id}/booking/appointments?date_from=${dateFilter}&date_to=${dateFilter}`).then(r => r.json()).then(d => { setAppointments(d.appointments || []); setLoading(false); });
    fetch(`${API_BASE}/api/org/${id}/booking/services`).then(r => r.json()).then(d => setServices(d.services || []));
    fetch(`${API_BASE}/api/org/${id}/booking/staff`).then(r => r.json()).then(d => setStaff(d.staff || []));
  };

  useEffect(() => { if (orgId) loadAll(); }, [dateFilter]);

  const createAppointment = async () => {
    if (!custName || !apptDate || !apptTime) return;
    setCreating(true);
    const duration = services.find(s => s.id === apptServiceId)?.duration_minutes || 60;
    const [h, m] = apptTime.split(":").map(Number);
    const endH = h + Math.floor((m + duration) / 60);
    const endM = (m + duration) % 60;
    const endTime = `${String(endH).padStart(2, "0")}:${String(endM).padStart(2, "0")}`;

    try {
      await fetch(`${API_BASE}/api/org/${orgId}/booking/appointments`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_name: custName, customer_phone: custPhone,
          date: apptDate, start_time: apptTime, end_time: endTime,
          service_id: apptServiceId || undefined, staff_id: apptStaffId || undefined,
          notes: apptNotes, source: "manual",
        }),
      });
      setShowCreate(false); setCustName(""); setCustPhone(""); setApptNotes("");
      loadAll();
    } catch (e) { console.error(e); }
    finally { setCreating(false); }
  };

  const createService = async () => {
    if (!svcName) return;
    await fetch(`${API_BASE}/api/org/${orgId}/booking/services`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: svcName, duration_minutes: svcDuration, price: svcPrice }),
    });
    setShowService(false); setSvcName(""); setSvcDuration(60); setSvcPrice(0);
    loadAll();
  };

  const updateStatus = async (apptId: string, status: string) => {
    await fetch(`${API_BASE}/api/org/${orgId}/booking/appointments/${apptId}`, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    loadAll();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <a href={`/dashboard/${orgSlug}`} className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <Calendar className="w-6 h-6 text-indigo-600" />
            <div>
              <h1 className="text-lg font-bold">Booking</h1>
              <p className="text-xs text-gray-500">{appointments.length} appointments today</p>
            </div>
          </div>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700">
            <Plus className="w-3.5 h-3.5" /> New Appointment
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4">
        {/* Tabs */}
        <div className="flex gap-1 mb-4 bg-gray-100 p-1 rounded-lg w-fit">
          <button onClick={() => setTab("appointments")} className={`px-4 py-1.5 rounded-md text-xs font-medium transition ${tab === "appointments" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}>Appointments</button>
          <button onClick={() => setTab("services")} className={`px-4 py-1.5 rounded-md text-xs font-medium transition ${tab === "services" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}>Services</button>
          <button onClick={() => setTab("staff")} className={`px-4 py-1.5 rounded-md text-xs font-medium transition ${tab === "staff" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}>Staff</button>
        </div>

        {tab === "appointments" && (
          <>
            {/* Date picker */}
            <div className="flex items-center gap-3 mb-4">
              <button onClick={() => { const d = new Date(dateFilter); d.setDate(d.getDate() - 1); setDateFilter(d.toISOString().split("T")[0]); }} className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm hover:bg-gray-50">&larr;</button>
              <input type="date" value={dateFilter} onChange={e => setDateFilter(e.target.value)} className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm" />
              <button onClick={() => { const d = new Date(dateFilter); d.setDate(d.getDate() + 1); setDateFilter(d.toISOString().split("T")[0]); }} className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm hover:bg-gray-50">&rarr;</button>
              <button onClick={() => setDateFilter(new Date().toISOString().split("T")[0])} className="px-3 py-1.5 text-xs text-indigo-600 hover:underline">Today</button>
            </div>

            {/* Appointments list */}
            <div className="space-y-2">
              {loading ? <p className="text-center text-sm text-gray-400 py-8">Loading...</p> :
               appointments.length === 0 ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                  <Calendar className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No appointments for this date</p>
                </div>
              ) : appointments.map(a => (
                <div key={a.id} className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-center min-w-[60px]">
                      <p className="text-lg font-bold text-gray-900">{a.start_time?.slice(0, 5)}</p>
                      <p className="text-[10px] text-gray-400">{a.end_time?.slice(0, 5)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{a.customer_name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {a.customer_phone && <span className="text-xs text-gray-500 flex items-center gap-1"><Phone className="w-3 h-3" />{a.customer_phone}</span>}
                        {a.booking_services && <span className="text-xs text-indigo-600">{a.booking_services.name}</span>}
                        {a.booking_staff && <span className="text-xs text-gray-400">with {a.booking_staff.name}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[a.status]}`}>{a.status}</span>
                    {a.status === "confirmed" && (
                      <button onClick={() => updateStatus(a.id, "completed")} className="p-1.5 rounded-lg bg-green-50 text-green-600 hover:bg-green-100" title="Mark completed">
                        <Check className="w-3.5 h-3.5" />
                      </button>
                    )}
                    {a.status !== "cancelled" && a.status !== "completed" && (
                      <button onClick={() => updateStatus(a.id, "cancelled")} className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100" title="Cancel">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {tab === "services" && (
          <div>
            <div className="flex justify-end mb-3">
              <button onClick={() => setShowService(true)} className="text-xs text-indigo-600 hover:underline flex items-center gap-1"><Plus className="w-3 h-3" /> Add Service</button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {services.map(s => (
                <div key={s.id} className="bg-white rounded-xl border border-gray-200 p-4">
                  <h3 className="text-sm font-semibold text-gray-900">{s.name}</h3>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{s.duration_minutes} min</span>
                    {s.price > 0 && <span>₹{s.price}</span>}
                  </div>
                </div>
              ))}
              {services.length === 0 && <p className="text-sm text-gray-400 col-span-3 text-center py-8">No services. Add one to get started.</p>}
            </div>
          </div>
        )}

        {tab === "staff" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {staff.map(s => (
              <div key={s.id} className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                  <User className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{s.name}</p>
                  {s.phone && <p className="text-xs text-gray-500">{s.phone}</p>}
                </div>
              </div>
            ))}
            {staff.length === 0 && <p className="text-sm text-gray-400 col-span-3 text-center py-8">No staff members added yet.</p>}
          </div>
        )}
      </main>

      {/* Create Appointment Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">New Appointment</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Customer Name *</label>
                <input type="text" value={custName} onChange={e => setCustName(e.target.value)} placeholder="Customer name"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Phone</label>
                <input type="tel" value={custPhone} onChange={e => setCustPhone(e.target.value)} placeholder="9876543210"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Date *</label>
                  <input type="date" value={apptDate} onChange={e => setApptDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Time *</label>
                  <input type="time" value={apptTime} onChange={e => setApptTime(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Service</label>
                  <select value={apptServiceId} onChange={e => setApptServiceId(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
                    <option value="">Select service</option>
                    {services.map(s => <option key={s.id} value={s.id}>{s.name} ({s.duration_minutes}min)</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Staff</label>
                  <select value={apptStaffId} onChange={e => setApptStaffId(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
                    <option value="">Any available</option>
                    {staff.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Notes</label>
                <input type="text" value={apptNotes} onChange={e => setApptNotes(e.target.value)} placeholder="Any notes..."
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
              </div>
              <button onClick={createAppointment} disabled={creating || !custName || !apptDate || !apptTime}
                className="w-full py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
                {creating ? "Creating..." : "Book Appointment"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Service Modal */}
      {showService && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowService(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Add Service</h2>
              <button onClick={() => setShowService(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-600 block mb-1">Service Name *</label>
                <input type="text" value={svcName} onChange={e => setSvcName(e.target.value)} placeholder="e.g., Haircut, Consultation"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Duration (min)</label>
                  <input type="number" value={svcDuration} onChange={e => setSvcDuration(parseInt(e.target.value) || 60)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Price (₹)</label>
                  <input type="number" value={svcPrice} onChange={e => setSvcPrice(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                </div>
              </div>
              <button onClick={createService} disabled={!svcName}
                className="w-full py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
                Add Service
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}