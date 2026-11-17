import api from "./api.js";

export const authApi = {
  me: () => api.get("/auth/me"),
  login: (credentials, isAdmin = false) =>
    api.post(isAdmin ? "/auth/admin/login" : "/auth/login", credentials),
  register: (registration) => api.post("/auth/register", registration),
  logout: () => api.post("/auth/logout"),
};
