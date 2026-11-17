import api from "./api.js";

const pageParams = (params = {}) => ({ skip: 0, limit: 50, ...params });

export const stopsApi = {
  list: (params) => api.get("/stops", { params: pageParams(params) }),
  get: (id) => api.get(`/stops/${id}`),
  create: (payload) => api.post("/stops", payload),
  update: (id, payload) => api.patch(`/stops/${id}`, payload),
};
