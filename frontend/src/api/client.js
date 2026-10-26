export const SERVER_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/api\/?$/, "").replace(/\/$/, "");
export const API_BASE = `${SERVER_BASE}/api`;

export function getMediaUrl(path) {
  if (!path) return "";
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${SERVER_BASE}${cleanPath}`;
}

export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const token = typeof localStorage !== "undefined" ? localStorage.getItem("rt_token") : null;
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let errMessage = `API Error ${response.status}`;
    try {
      const errData = await response.json();
      if (typeof errData.detail === "string") {
        errMessage = errData.detail;
      } else if (Array.isArray(errData.detail)) {
        errMessage = errData.detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
      } else if (errData.detail) {
        errMessage = JSON.stringify(errData.detail);
      } else if (errData.msg) {
        errMessage = errData.msg;
      }
    } catch (_) { }
    const error = new Error(errMessage);
    error.status = response.status;   // ← AuthModal usa err.status === 403
    throw error;
  }

  return response.json();
}

// ── Helpers de usuario ───────────────────────────────────────────────────

/**
 * true si el usuario tiene acceso Pro (por rol o por suscripción).
 * Acepta tanto `is_premium` (backend) como `isPremium` (algunos componentes).
 */
export function hasPremiumAccess(user) {
  if (!user) return false;
  if (user.role === "Super Admin") return true;
  return user.is_premium === true || user.isPremium === true;
}

// ── Auth ─────────────────────────────────────────────────────────────────

export async function verifyEmailToken(token) {
  const res = await fetch(`${API_BASE}/auth/verify-email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    // FastAPI devuelve `detail`, no `error`.
    throw new Error(errorData.detail || errorData.error || "Token inválido o expirado");
  }

  return await res.json();
}

export async function registerUser(email, password) {
  const data = await apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  // FIX: el token viene en `data.token`, no en `data.user.token`.
  // En este backend /register no devuelve token (requiere verificar correo),
  // pero por si en el futuro se añade auto-login, lo dejamos tolerante.
  if (data?.token) {
    localStorage.setItem("rt_token", data.token);
  }
  return data;
}

export async function loginUser(email, password) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  // FIX: token en `data.token` (nivel raíz), no `data.user.token`.
  if (data?.token) {
    localStorage.setItem("rt_token", data.token);
  }
  return data;
}

export async function fetchCurrentUser() {
  return apiRequest("/auth/me");
}

export async function resendVerificationEmail(email) {
  return apiRequest("/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function logoutUser() {
  localStorage.removeItem("rt_token");
}

// ── Pagos ────────────────────────────────────────────────────────────────

export async function getPaymentConfig() {
  return apiRequest("/payments/config");
}

export async function createCheckout() {
  return apiRequest("/payments/checkout", { method: "POST" });
}

export async function confirmCheckout(sessionId) {
  return apiRequest("/payments/confirm", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function simulatePayment(outcome = "approved") {
  return apiRequest("/payments/simulate", {
    method: "POST",
    body: JSON.stringify({ outcome }),
  });
}

// ── Settings ─────────────────────────────────────────────────────────────

export async function fetchSettings() {
  return apiRequest("/settings");
}

export async function updateSettings(settings) {
  return apiRequest("/settings", {
    method: "PUT",
    body: JSON.stringify({ settings }),
  });
}

export async function revealSetting(key) {
  return apiRequest("/settings/reveal", {
    method: "POST",
    body: JSON.stringify({ key }),
  });
}

export async function testServiceCredentials(service) {
  return apiRequest(`/settings/test/${service}`, { method: "POST" });
}

// ── Assets / Library / Uploads ───────────────────────────────────────────

export async function fetchAssets() {
  return apiRequest("/assets");
}

export async function fetchLibrary() {
  return apiRequest("/library");
}

export async function uploadMediaFile(category, file) {
  const formData = new FormData();
  formData.append("file", file);

  const endpoint = category === "background_video" ? "/upload/background_video" : "/upload/background_audio";
  const token = typeof localStorage !== "undefined" ? localStorage.getItem("rt_token") : null;
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  // FIX: usar API_BASE y enviar Authorization. NO poner Content-Type
  // manualmente con FormData: el navegador debe generar el boundary.
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    body: formData,
    headers,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    const error = new Error(errData.detail || "Fallo al subir archivo");
    error.status = response.status;
    throw error;
  }

  return response.json();
}

// ── Proyectos ────────────────────────────────────────────────────────────

export async function createProject(payload = {}) {
  return apiRequest("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getProject(projectId) {
  return apiRequest(`/projects/${projectId}`);
}

export async function updateProject(projectId, data) {
  return apiRequest(`/projects/${projectId}`, {
    method: "PUT",
    body: JSON.stringify({ data }),
  });
}

export async function listProjects() {
  return apiRequest("/projects");
}

export async function runProjectStep(projectId, stepName, args = {}) {
  return apiRequest(`/projects/${projectId}/steps/${stepName}`, {
    method: "POST",
    body: JSON.stringify({ args }),
  });
}

export async function cancelJob(jobId) {
  return apiRequest(`/jobs/${jobId}/cancel`, { method: "POST" });
}

// ── Storage ──────────────────────────────────────────────────────────────

export async function fetchStorageStatus() {
  return apiRequest("/storage/status");
}

export async function triggerStorageCleanup() {
  return apiRequest("/storage/cleanup", { method: "POST" });
}

// ── Validaciones ─────────────────────────────────────────────────────────

export async function validateVideoLink(url) {
  return apiRequest("/links/validate_video", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

// ── SSE ──────────────────────────────────────────────────────────────────

export function subscribeJobEvents(jobId, onEvent, onError, onComplete) {
  const eventSource = new EventSource(`${API_BASE}/jobs/${jobId}/events`);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "done") {
        onEvent(data);
        eventSource.close();
        if (onComplete) onComplete(data);
      } else if (data.type === "error" && data.level === "error") {
        onEvent(data);
        eventSource.close();
        if (onError) onError(data);
      } else {
        onEvent(data);
      }
    } catch (e) {
      console.error("SSE parse error", e);
    }
  };

  eventSource.onerror = (err) => {
    console.error("SSE Connection error", err);
    eventSource.close();
    if (onError) onError(err);
  };

  return () => eventSource.close();
}