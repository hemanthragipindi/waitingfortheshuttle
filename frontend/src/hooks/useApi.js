import { useCallback, useEffect, useState } from "react";

export function getApiError(error, fallback = "The request could not be completed.") {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join(" ");
  }
  if (!error.response) return "Could not connect to the service. Check your connection and try again.";
  return fallback;
}

export function useApi(load, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await load();
      setData(response.data);
      return response.data;
    } catch (requestError) {
      setError(getApiError(requestError, "Unable to load this information."));
      return null;
    } finally {
      setLoading(false);
    }
  // `load` is intentionally supplied by the caller alongside explicit dependencies.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, setData, loading, error, refresh };
}
