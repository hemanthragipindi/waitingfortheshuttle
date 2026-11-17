import api from "./api.js";

const pageParams = (params = {}) => ({ skip: 0, limit: 50, ...params });

export const announcementsApi = {
  list: (params) => api.get("/announcements", { params: pageParams(params) }),
  get: (id) => api.get(`/announcements/${id}`),
  create: (payload) => api.post("/announcements", payload),
  update: (id, payload) => api.patch(`/announcements/${id}`, payload),
  remove: (id) => api.delete(`/announcements/${id}`),
};
