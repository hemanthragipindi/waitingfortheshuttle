import api from "./api.js";

const pageParams = (params = {}) => ({ skip: 0, limit: 50, ...params });

export const feedbackApi = {
  create: (payload) => api.post("/feedback", payload),
  mine: (params) => api.get("/feedback/mine", { params: pageParams(params) }),
  list: (params) => api.get("/feedback", { params: pageParams(params) }),
  get: (id) => api.get(`/feedback/${id}`),
  updateStatus: (id, payload) => api.patch(`/feedback/${id}/status`, payload),
};
