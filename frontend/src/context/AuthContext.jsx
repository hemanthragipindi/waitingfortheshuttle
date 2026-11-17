import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "../services/auth.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    let active = true;
    authApi
      .me()
      .then(({ data }) => {
        if (active) setUser(data);
      })
      .catch((error) => {
        if (active && error.response?.status !== 401) {
          setAuthError("Unable to check your sign-in session. Please refresh the page.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (credentials, isAdmin = false) => {
    const { data } = await authApi.login(credentials, isAdmin);
    setUser(data);
    setAuthError("");
    return data;
  }, []);

  const register = useCallback(async (registration) => {
    const { data } = await authApi.register(registration);
    setUser(data);
    setAuthError("");
    return data;
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
    setAuthError("");
  }, []);

  const value = useMemo(
    () => ({ user, loading, authError, login, register, logout }),
    [user, loading, authError, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside an AuthProvider.");
  }
  return context;
}
