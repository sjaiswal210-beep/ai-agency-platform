const API_URL = "https://ai-agency-platform.onrender.com";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  dashboard: {
    stats: () => fetchAPI<DashboardStats>("/dashboard/stats"),
    activity: (limit = 20) => fetchAPI<ActivityLog[]>(`/dashboard/activity?limit=${limit}`),
  },
  leads: {
    list: (status?: string) =>
      fetchAPI<Lead[]>(`/leads/${status ? `?status=${status}` : ""}`),
    get: (id: string) => fetchAPI<Lead>(`/leads/${id}`),
    create: (data: Partial<Lead>) =>
      fetchAPI<Lead>("/leads/", { method: "POST", body: JSON.stringify(data) }),
    discover: (location: string, category: string, count: number = 10) =>
      fetchAPI<{ discovered: number; leads: Lead[] }>(
        `/leads/discover?location=${encodeURIComponent(location)}&category=${encodeURIComponent(category)}&count=${count}`,
        { method: "POST" }
      ),
    analyze: (id: string) =>
      fetchAPI<AnalysisResponse>(`/leads/${id}/analyze`, { method: "POST" }),
  },
  websites: {
    generate: (leadId: string, template: string) =>
      fetchAPI<Website>(
        `/websites/generate?lead_id=${leadId}&template=${template}`,
        { method: "POST" }
      ),
    getForLead: (leadId: string) => fetchAPI<Website[]>(`/websites/lead/${leadId}`),
    list: () => fetchAPI<Website[]>("/websites/"),
    deploy: (websiteId: string) =>
      fetchAPI(`/websites/${websiteId}/deploy`, { method: "POST" }),
  },
  outreach: {
    send: (leadId: string, channel: string) =>
      fetchAPI(`/outreach/send?lead_id=${leadId}&channel=${channel}`, { method: "POST" }),
    followup: (leadId: string) =>
      fetchAPI(`/outreach/followup/${leadId}`, { method: "POST" }),
    history: (leadId: string) => fetchAPI<OutreachMessage[]>(`/outreach/lead/${leadId}`),
  },
};

export interface DashboardStats {
  total_leads: number;
  total_websites: number;
  total_outreach: number;
  leads_by_status: Record<string, number>;
  conversion_rate: number;
}

export interface Lead {
  id: string;
  business_name: string;
  owner_name?: string;
  phone?: string;
  email?: string;
  website?: string;
  address?: string;
  category?: string;
  rating?: number;
  review_count?: number;
  status: string;
  opportunity_score?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Website {
  id: string;
  lead_id: string;
  template: string;
  preview_url?: string;
  deployed_url?: string;
  status: string;
  content?: Record<string, unknown>;
  created_at: string;
}

export interface OutreachMessage {
  id: string;
  lead_id: string;
  channel: string;
  message: string;
  status: string;
  sent_at?: string;
  created_at: string;
}

export interface AnalysisResponse {
  lead_id: string;
  score: number;
  analysis: Record<string, unknown>;
}

export interface ActivityLog {
  id: string;
  agent_name: string;
  action: string;
  lead_id?: string;
  details?: Record<string, unknown>;
  created_at: string;
}
