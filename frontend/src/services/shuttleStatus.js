import api from "./api.js";

const pageParams = (params = {}) => ({ skip: 0, limit: 50, ...params });

export const shuttleStatusApi = {
  list: (params) => api.get("/shuttle-status", { params: pageParams(params) }),
  byRoute: (routeId, params) =>
    api.get(`/shuttle-status/route/${routeId}`, { params: pageParams(params) }),
  current: (shuttleId) => api.get(`/shuttle-status/shuttle/${shuttleId}`),
  history: (shuttleId, params) =>
    api.get(`/shuttle-status/shuttle/${shuttleId}/history`, {
      params: pageParams(params),
    }),
  create: (payload) => api.post("/shuttle-status", payload),
};
