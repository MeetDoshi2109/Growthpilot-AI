/**
 * GrowthPilot API client
 * All requests go through Next.js rewrites → backend
 */
import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
  : "/api/v1";

export const api = axios.create({
  baseURL: BASE,
  withCredentials: true, // send httpOnly JWT cookies
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  logout: () => api.post("/auth/logout"),
  me: () => api.get("/auth/me"),
};

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const dashboardApi = {
  kpis: () => api.get("/dashboard/kpis"),
  revenue: (days = 30) => api.get(`/dashboard/revenue?days=${days}`),
  attribution: (days = 14) => api.get(`/dashboard/attribution?days=${days}`),
  retention: (days = 30) => api.get(`/dashboard/retention?days=${days}`),
  inventoryRisks: () => api.get("/dashboard/inventory-risks"),
  inactiveCustomers: () => api.get("/dashboard/inactive-customers"),
  overduePayments: () => api.get("/dashboard/overdue-payments"),
};

// ── Opportunities ─────────────────────────────────────────────────────────────
export const opportunitiesApi = {
  list: (refresh = false) =>
    api.get(`/opportunities?refresh=${refresh}`),
  get: (id: string) => api.get(`/opportunities/${id}`),
};

// ── Actions ───────────────────────────────────────────────────────────────────
export const actionsApi = {
  propose: (payload: {
    opportunity_id?: string;
    action_type: string;
    params?: Record<string, unknown>;
    estimated_impact_paise?: number;
  }) => api.post("/actions/propose", payload),
  approve: (id: string, editedParams?: Record<string, unknown>, note?: string) =>
    api.post(`/actions/${id}/approve`, { edited_params: editedParams, note }),
  reject: (id: string, reason?: string) =>
    api.post(`/actions/${id}/reject`, null, { params: { reason } }),
  list: (status?: string) =>
    api.get(`/actions${status ? `?status=${status}` : ""}`),
  get: (id: string) => api.get(`/actions/${id}`),
};

// ── Audit ─────────────────────────────────────────────────────────────────────
export const auditApi = {
  list: (params?: { limit?: number; offset?: number; tool?: string }) =>
    api.get("/audit", { params }),
  verify: () => api.get("/audit/verify"),
};

// ── Assistant ─────────────────────────────────────────────────────────────────
export const assistantApi = {
  chat: (message: string, sessionId?: string) =>
    api.post("/assistant/chat", { message, session_id: sessionId }),
};

// ── Missions ──────────────────────────────────────────────────────────────────
export const missionsApi = {
  create: (goal: string, title?: string) =>
    api.post("/missions", { goal, title }),
  get: (id: string) => api.get(`/missions/${id}`),
  stream: (id: string) =>
    new EventSource(`${BASE}/missions/${id}/stream`, { withCredentials: true }),
};

// ── Health ────────────────────────────────────────────────────────────────────
export const systemApi = {
  health: () => api.get("/health".replace("/api/v1", ""), { baseURL: BASE.replace("/api/v1", "") }),
};
