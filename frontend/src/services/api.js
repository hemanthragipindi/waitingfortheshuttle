import axios from "axios";

const csrfCookieName = import.meta.env.VITE_CSRF_COOKIE_NAME || "p05_csrf_token";

function getApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
  const apiUrl = new URL(configuredUrl, window.location.origin);
  const localHosts = new Set(["localhost", "127.0.0.1", "[::1]"]);

  if (
    localHosts.has(window.location.hostname)
    && localHosts.has(apiUrl.hostname)
  ) {
    apiUrl.hostname = window.location.hostname;
  }

  return apiUrl.toString().replace(/\/$/, "");
}

function readCookie(name) {
  const entry = document.cookie
    .split("; ")
    .find((cookie) => cookie.startsWith(`${name}=`));

  return entry ? decodeURIComponent(entry.slice(name.length + 1)) : null;
}

const api = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  if (["post", "put", "patch", "delete"].includes(config.method?.toLowerCase())) {
    const csrfToken = readCookie(csrfCookieName);
    if (csrfToken) {
      config.headers["X-CSRF-Token"] = csrfToken;
    }
  }
  return config;
});

export default api;
