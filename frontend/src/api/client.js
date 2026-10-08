const API_BASE = "/api";

export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let errMessage = `API Error ${response.status}`;
    try {
      const errData = await response.json();
      errMessage = errData.detail || errData.msg || errMessage;
    } catch (_) {}
    throw new Error(errMessage);
  }

  return response.json();
}

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

export async function fetchAssets() {
  return apiRequest("/assets");
}

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

export async function fetchLibrary() {
  return apiRequest("/library");
}

export async function uploadMediaFile(category, file) {
  const formData = new FormData();
  formData.append("file", file);

  const endpoint = category === "background_video" ? "/upload/background_video" : "/upload/background_audio";
  const response = await fetch(`/api${endpoint}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Fallo al subir archivo");
  }

  return response.json();
}

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
