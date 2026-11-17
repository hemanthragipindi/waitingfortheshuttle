import api from "./api.js";

const pageParams = (params = {}) => ({ skip: 0, limit: 50, ...params });

export const shuttlesApi = {
  list: (params) => api.get("/shuttles", { params: pageParams(params) }),
  get: (id) => api.get(`/shuttles/${id}`),
  create: (payload) => api.post("/shuttles", payload),
  update: (id, payload) => api.patch(`/shuttles/${id}`, payload),
};
