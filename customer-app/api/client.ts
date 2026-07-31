/**
 * Typed REST client for the GroceryGo Flask backend. Every function here
 * calls a real /api/* endpoint — there is no mock data or hardcoded arrays
 * anywhere in this file or in GroceryGoApp.tsx.
 */

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || "";

const TOKEN_KEY = "gg_access_token";
const REFRESH_KEY = "gg_refresh_token";
const USER_KEY = "gg_user";

export interface User {
  id: number;
  name: string;
  email: string;
  phone?: string | null;
  role: string;
  is_active: boolean;
}

export interface Category {
  id: number;
  name: string;
  description?: string | null;
  image_url?: string | null;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  description?: string | null;
  category_id: number | null;
  category: string | null;
  price: number;
  unit: string;
  image_url?: string | null;
  is_active: boolean;
  stock_quantity?: number;
  low_stock?: boolean;
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Order {
  id: number;
  customer_id: number;
  status: string;
  total_amount: number;
  delivery_address: string;
  assigned_delivery_id: number | null;
  placed_at: string;
  updated_at: string;
  items?: OrderItem[];
}

export interface Payment {
  id: number;
  order_id: number;
  method: string;
  amount: number;
  status: string;
  razorpay_order_id?: string | null;
  razorpay_payment_id?: string | null;
  transaction_ref?: string | null;
}

export interface Customer {
  id: number;
  user_id: number;
  name: string;
  email: string;
  phone: string | null;
  address: string | null;
  city: string | null;
  pincode: string | null;
  loyalty_points: number;
}

export interface Notification {
  id: number;
  user_id: number | null;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

function storeSession(access: string, refresh: string, user: User) {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn(): boolean {
  return !!getAccessToken();
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  const res = await fetch(`${API_BASE}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return false;
  const body = await res.json();
  localStorage.setItem(TOKEN_KEY, body.data.access_token);
  return true;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const token = getAccessToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && retry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return request<T>(path, options, false);
    clearSession();
    throw new ApiError("Session expired. Please log in again.", 401);
  }

  const contentType = res.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await res.json() : null;

  if (!res.ok) {
    throw new ApiError((body && body.error) || `Request failed (${res.status})`, res.status);
  }
  return (body ? body.data : undefined) as T;
}

// ---------------- Auth ----------------
export async function login(email: string, password: string): Promise<User> {
  const data = await request<{ access_token: string; refresh_token: string; user: User }>(
    "/api/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) }
  );
  storeSession(data.access_token, data.refresh_token, data.user);
  return data.user;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  phone?: string;
  address?: string;
  city?: string;
  pincode?: string;
}

export async function register(payload: RegisterPayload): Promise<User> {
  return request<User>("/api/auth/register", { method: "POST", body: JSON.stringify(payload) });
}

export async function fetchMe(): Promise<User> {
  return request<User>("/api/auth/me");
}

// ---------------- Catalog ----------------
export async function fetchCategories(): Promise<Category[]> {
  return request<Category[]>("/api/categories");
}

export interface ProductFilters {
  search?: string;
  category_id?: number;
  page?: number;
  per_page?: number;
}

export async function fetchProducts(filters: ProductFilters = {}): Promise<Product[]> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.category_id) params.set("category_id", String(filters.category_id));
  params.set("page", String(filters.page || 1));
  params.set("per_page", String(filters.per_page || 50));
  return request<Product[]>(`/api/products?${params.toString()}`);
}

// ---------------- Customer profile ----------------
export async function fetchCustomerProfile(customerId: number): Promise<Customer> {
  return request<Customer>(`/api/customers/${customerId}`);
}

export async function updateCustomerProfile(
  customerId: number,
  payload: Partial<Pick<Customer, "name" | "phone" | "address" | "city" | "pincode">>
): Promise<Customer> {
  return request<Customer>(`/api/customers/${customerId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

// ---------------- Orders ----------------
export interface CartLine {
  product_id: number;
  quantity: number;
}

export async function placeOrder(items: CartLine[], deliveryAddress: string): Promise<Order> {
  return request<Order>("/api/orders", {
    method: "POST",
    body: JSON.stringify({ items, delivery_address: deliveryAddress }),
  });
}

export async function fetchMyOrders(): Promise<Order[]> {
  return request<Order[]>("/api/orders?sort_by=placed_at&sort_dir=desc&per_page=100");
}

export async function fetchOrder(orderId: number): Promise<Order> {
  return request<Order>(`/api/orders/${orderId}`);
}

export async function trackOrder(orderId: number) {
  return request<{ order_id: number; status: string; assigned_delivery_id: number | null; updated_at: string }>(
    `/api/orders/${orderId}/track`
  );
}

export async function cancelOrder(orderId: number): Promise<Order> {
  return request<Order>(`/api/orders/${orderId}/cancel`, { method: "POST" });
}

// ---------------- Payments ----------------
export interface InitiatePaymentResult {
  payment: Payment;
  razorpay_key_id?: string;
  razorpay_order_id?: string;
  amount?: number;
  currency?: string;
  upi_link?: string;
  qr_code_path?: string;
}

export async function initiatePayment(
  orderId: number,
  method: "upi" | "card" | "netbanking" | "cash"
): Promise<InitiatePaymentResult> {
  return request<InitiatePaymentResult>(`/api/payments/orders/${orderId}/initiate`, {
    method: "POST",
    body: JSON.stringify({ method }),
  });
}

export async function verifyRazorpayPayment(payload: {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}): Promise<Payment> {
  return request<Payment>("/api/payments/razorpay/verify", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function verifyUpiPayment(payload: {
  payment_id: number;
  token: string;
  transaction_ref: string;
}): Promise<Payment> {
  return request<Payment>("/api/payments/upi/verify", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---------------- Notifications ----------------
export async function fetchNotifications(): Promise<Notification[]> {
  return request<Notification[]>("/api/notifications?per_page=50");
}

export async function markNotificationRead(id: number): Promise<Notification> {
  return request<Notification>(`/api/notifications/${id}/read`, { method: "PUT" });
}

// ---------------- Branding / Theme ----------------
export async function fetchBranding() {
  return request<{ app_name: string; logo_url: string | null; primary_color: string; secondary_color: string }>(
    "/api/branding"
  );
}

export async function fetchActiveTheme() {
  return request<{ theme_name: string; colors: Record<string, string> }>("/api/themes/active");
}

export { ApiError };
