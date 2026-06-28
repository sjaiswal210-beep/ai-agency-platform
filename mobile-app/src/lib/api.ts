const API_BASE = "https://ai-agency-platform.onrender.com";

export async function sendOTP(phone: string) {
  const res = await fetch(`${API_BASE}/api/mobile-auth/send-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to send OTP");
  }
  return res.json();
}

export async function verifyOTP(phone: string, otp: string) {
  const res = await fetch(`${API_BASE}/api/mobile-auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, otp }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Invalid OTP");
  }
  return res.json();
}

export async function fetchDashboard(orgId: string, token: string) {
  const res = await fetch(`${API_BASE}/api/organizations/${orgId}/modules`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

export async function fetchCRMContacts(orgId: string, token: string) {
  const res = await fetch(`${API_BASE}/api/org/${orgId}/crm/contacts?limit=50`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

export async function fetchBookings(orgId: string, token: string) {
  const res = await fetch(`${API_BASE}/api/org/${orgId}/bookings`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

export { API_BASE };