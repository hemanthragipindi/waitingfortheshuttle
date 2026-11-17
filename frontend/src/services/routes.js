import api from "./api.js";

const pageParams = (params = {}) => ({ skip: 0, limit: 50, ...params });

export const routesApi = {
  list: (params) => api.get("/routes", { params: pageParams(params) }),
  get: (id) => api.get(`/routes/${id}`),
  create: (payload) => api.post("/routes", payload),
  update: (id, payload) => api.patch(`/routes/${id}`, payload),
  addStop: (id, payload) => api.post(`/routes/${id}/stops`, payload),
  orderStops: (id, payload) => api.put(`/routes/${id}/stops/order`, payload),
  removeStop: (routeId, stopId) => api.delete(`/routes/${routeId}/stops/${stopId}`),
};
