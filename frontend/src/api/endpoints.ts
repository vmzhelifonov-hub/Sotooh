/** Typed API endpoints. */
import { api } from "./client";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  organization_id: string | null;
  organization_name: string | null;
  role: "owner" | "member" | null;
  is_staff: boolean;
}

export interface Organization {
  id: string;
  company_name: string;
  company_name_ar: string;
  logo: string | null;
  logo_url: string | null;
  phone: string;
  email: string;
  address: string;
  city: string;
  country: string;
  preferred_language: string;
  currency: string;
  timezone: string;
  quote_prefix: string;
  onboarding_completed: boolean;
}

export interface Customer {
  id: string;
  name: string;
  phone: string;
  secondary_phone: string;
  email: string;
  city: string;
  address: string;
  source: string;
  notes: string;
  stage: string;
  lost_reason: string;
  assigned_user: string | null;
  next_follow_up: string | null;
  created_at: string;
}

export interface Product {
  id: string;
  type: string;
  category: string;
  brand: string;
  model: string;
  sku: string;
  name_ar: string;
  name_en: string;
  description: string;
  cost_price: string;
  selling_price: string;
  currency: string;
  warranty_months: number;
  unit: string;
  active: boolean;
  image_url: string | null;
}

export interface QuoteItem {
  id?: string;
  product: string | null;
  description: string;
  brand_model: string;
  quantity: string;
  unit: string;
  unit_price: string;
  discount_amount: string;
  line_total: string;
  display_order: number;
}

export interface Quote {
  id: string;
  quote_number: string;
  customer: string;
  customer_name: string;
  customer_phone: string;
  customer_city?: string;
  status: string;
  issue_date: string;
  valid_until: string | null;
  currency: string;
  subtotal: string;
  discount_amount: string;
  discount_percent: string;
  tax_percent: string;
  tax_amount: string;
  total: string;
  notes_ar: string;
  notes_en: string;
  payment_terms: string;
  delivery_terms: string;
  items: QuoteItem[];
  share_enabled: boolean;
  share_url: string;
  pdf_url: string;
  pdf_generated_at: string | null;
  first_viewed_at: string | null;
  last_viewed_at: string | null;
  view_count: number;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface DashboardData {
  leads_this_month: number;
  quotes_this_month: number;
  quote_value_this_month: string;
  won_value: string;
  won_deals: number;
  conversion_rate: number;
  average_quote_value: string;
  overdue_follow_ups: number;
  funnel: { new: number; quote_sent: number; won: number };
  needs_attention: { id: string; name: string; phone: string; next_follow_up: string }[];
  recent_quotes: {
    id: string;
    quote_number: string;
    customer_name: string;
    status: string;
    total: string;
    currency: string;
    created_at: string;
  }[];
}

export interface SubscriptionInfo {
  plan: string | null;
  plan_name?: string;
  status: string;
  is_active: boolean;
  ends_at: string | null;
}

// --------------------------------------------------------------- auth

export const authApi = {
  register: (data: { email: string; password: string; company_name: string }) =>
    api.post<{ user: User; csrf_token: string }>("/auth/register/", data).then((r) => r.data),
  login: (data: { email: string; password: string }) =>
    api.post<{ user: User; csrf_token: string }>("/auth/login/", data).then((r) => r.data),
  logout: () => api.post("/auth/logout/").then((r) => r.data),
  me: () => api.get<User>("/me/").then((r) => r.data),
  requestPasswordReset: (email: string) =>
    api.post("/auth/password/reset/", { email }).then((r) => r.data),
  confirmPasswordReset: (data: { uid: string; token: string; password: string }) =>
    api.post("/auth/password/reset/confirm/", data).then((r) => r.data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post("/auth/password/change/", data).then((r) => r.data),
};

// --------------------------------------------------------------- org

export const orgApi = {
  get: () => api.get<Organization>("/organization/").then((r) => r.data),
  update: (data: Partial<Organization>) =>
    api.patch<Organization>("/organization/", data).then((r) => r.data),
  members: () =>
    api
      .get<{ id: string; user: User; role: string; is_active: boolean }[]>("/members/")
      .then((r) => r.data),
  subscription: () => api.get<SubscriptionInfo>("/subscription/").then((r) => r.data),
};

// --------------------------------------------------------------- catalog

export interface ProductPayload {
  name_ar: string;
  name_en?: string;
  category: string;
  brand?: string;
  model?: string;
  sku?: string;
  description?: string;
  cost_price?: string;
  selling_price: string;
  warranty_months?: number;
  unit?: string;
  type?: string;
  active?: boolean;
}

export const productApi = {
  list: (params: { page?: number; search?: string; category?: string; active?: string }) =>
    api.get<Paginated<Product>>("/products/", { params }).then((r) => r.data),
  get: (id: string) => api.get<Product>(`/products/${id}/`).then((r) => r.data),
  create: (data: ProductPayload) => api.post<Product>("/products/", data).then((r) => r.data),
  update: (id: string, data: Partial<ProductPayload>) =>
    api.patch<Product>(`/products/${id}/`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/products/${id}/`).then((r) => r.data),
  categories: () => api.get<{ value: string; label: string }[]>("/products/categories/").then((r) => r.data),
};

// --------------------------------------------------------------- crm

export const customerApi = {
  list: (params: { page?: number; search?: string; stage?: string; source?: string }) =>
    api.get<Paginated<Customer>>("/customers/", { params }).then((r) => r.data),
  get: (id: string) => api.get<Customer>(`/customers/${id}/`).then((r) => r.data),
  create: (data: Partial<Customer>) => api.post<Customer>("/customers/", data).then((r) => r.data),
  update: (id: string, data: Partial<Customer>) =>
    api.patch<Customer>(`/customers/${id}/`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/customers/${id}/`).then((r) => r.data),
  followupQueue: () =>
    api
      .get<{ overdue: Customer[]; today: Customer[]; upcoming: Customer[] }>("/customers/followup_queue/")
      .then((r) => r.data),
  meta: () =>
    api
      .get<{ sources: { value: string; label: string }[]; stages: { value: string; label: string }[] }>(
        "/customers/meta/"
      )
      .then((r) => r.data),
  completeFollowUp: (id: string) =>
    api.post<Customer>(`/customers/${id}/complete_follow_up/`).then((r) => r.data),
  scheduleFollowUp: (data: { customer: string; scheduled_for: string; note?: string }) =>
    api.post("/follow-ups/", data).then((r) => r.data),
};

// --------------------------------------------------------------- quotes

export const quoteApi = {
  list: (params: { page?: number; search?: string; status?: string }) =>
    api.get<Paginated<Quote>>("/quotes/", { params }).then((r) => r.data),
  get: (id: string) => api.get<Quote>(`/quotes/${id}/`).then((r) => r.data),
  create: (data: Record<string, unknown>) => api.post<Quote>("/quotes/", data).then((r) => r.data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch<Quote>(`/quotes/${id}/`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/quotes/${id}/`).then((r) => r.data),
  setStatus: (id: string, status: string, lost_reason?: string) =>
    api.post<Quote>(`/quotes/${id}/status/`, { status, lost_reason }).then((r) => r.data),
  generatePdf: (id: string) => api.post<{ pdf_url: string }>(`/quotes/${id}/pdf/`).then((r) => r.data),
  share: (id: string) =>
    api.post<{ share_url: string; share_enabled: boolean }>(`/quotes/${id}/share/`).then((r) => r.data),
  revokeShare: (id: string) => api.post(`/quotes/${id}/revoke_share/`).then((r) => r.data),
  duplicate: (id: string) => api.post<Quote>(`/quotes/${id}/duplicate/`).then((r) => r.data),
};

export const publicQuoteApi = {
  get: (token: string) =>
    api.get(`/public/quotes/${token}/`).then((r) => r.data as Record<string, unknown>),
};

// --------------------------------------------------------------- dashboard

export const dashboardApi = {
  get: () => api.get<DashboardData>("/dashboard/").then((r) => r.data),
};
