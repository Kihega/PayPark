/**
 * ParkiPay — API Service
 * Axios instance with:
 * - Base URL from constants (platform-aware)
 * - Extended timeout for Render free-tier cold starts (up to 50 s)
 * - Bearer token injection
 * - Silent 401 → refresh → retry logic
 * - Logout on unrecoverable 401
 * - Human-readable network error codes
 */
import axios, {
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig,
} from 'axios';
import { API_BASE_URL, API_ROUTES } from '@/constants/api';
import { useAuthStore } from '@/store/authStore';

// ── Axios instance ────────────────────────────────────────────────────────────

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // 50 s covers Render free-tier cold starts (typically 30–50 s after idle).
  // For local dev this is still fast because the server is already running.
  timeout: 50000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ── Request interceptor: attach Bearer token ──────────────────────────────────

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (__DEV__) {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
  }
  return config;
});

// ── Response interceptor: silent token refresh on 401 ────────────────────────

let isRefreshing = false;
let failedQueue: {
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}[] = [];

const processQueue = (error: unknown, token: string | null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // ── Network / timeout errors: enrich with a useful code ──────────────────
    if (!error.response) {
      const isTimeout = error.code === 'ECONNABORTED';
      const enriched = {
        ...error,
        response: {
          data: {
            error: isTimeout ? 'timeout' : 'network_error',
            detail: isTimeout
              ? 'The server took too long to respond. If it was idle it may be waking up — please try again in a moment.'
              : `Cannot reach the server at ${API_BASE_URL}. Check your network or update EXPO_PUBLIC_API_URL in mobile/.env.`,
          },
        },
      };
      return Promise.reject(enriched);
    }

    // ── 401: try a silent token refresh ──────────────────────────────────────
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = useAuthStore.getState().refreshToken;
      if (!refreshToken) {
        await useAuthStore.getState().clearAuth();
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(
          `${API_BASE_URL}${API_ROUTES.refresh}`,
          { refresh: refreshToken },
        );

        const newAccessToken: string = data.access;
        useAuthStore.getState().setAccessToken(newAccessToken);
        processQueue(null, newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        await useAuthStore.getState().clearAuth();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

// ── Typed helpers ─────────────────────────────────────────────────────────────

// ── Auth: ID-only login ───────────────────────────────────────────────────────
export const authService = {
  loginById: (employee_id: string) =>
    apiClient.post('/api/auth/login/', { employee_id }),
  logout: (refresh: string) =>
    apiClient.post('/api/auth/logout/', { refresh }),
  me: () => apiClient.get('/api/auth/me/'),
};

// ── Admin service ─────────────────────────────────────────────────────────────
export const adminService = {
  listOfficers:  ()                    => apiClient.get('/api/admin/officers/'),
  listLocations: ()                    => apiClient.get('/api/admin/locations/'),
  createOfficer: (body: object)        => apiClient.post('/api/admin/officers/', body),
  removeOfficer: (id: number)          => apiClient.delete(`/api/admin/officers/${id}/`),
  moveOfficer:   (id: number, locId: number) =>
    apiClient.patch(`/api/admin/officers/${id}/location/`, { locationId: locId }),
};

// ── Vehicle lookup service ────────────────────────────────────────────────────
export const vehicleService = {
  lookup:    (plate: string) => apiClient.get(`/api/vehicles/lookup/?plate=${encodeURIComponent(plate)}`),
  locations: ()              => apiClient.get('/api/vehicles/locations/'),
};

// ── Vehicle registry management (admin) ──────────────────────────────────────
export const vehicleRegistryService = {
  list:     ()              => apiClient.get('/api/admin/vehicles/'),
  register: (body: object)  => apiClient.post('/api/admin/vehicles/', body),
  remove:   (id: number)    => apiClient.delete(`/api/admin/vehicles/${id}/`),
};

// ── Billing service ───────────────────────────────────────────────────────────
export const billingService = {
  generate:   (plate_number: string, location_id: number) =>
    apiClient.post('/api/billing/generate/', { plate_number, location_id }),
  history:    () => apiClient.get('/api/billing/history/'),
  stats:      () => apiClient.get('/api/billing/stats/'),
  activeBill: (plate: string) =>
    apiClient.get(`/api/billing/active-bill/?plate=${encodeURIComponent(plate)}`),
  status:     (cn: string) => apiClient.get(`/api/billing/${cn}/status/`),
};
