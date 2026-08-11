import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { setAccessToken as setApiAccessToken, setUnauthorizedHandler } from "@/services/api";
import * as authService from "@/services/authService";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // If the api layer's silent-refresh-on-401 gives up, drop local session state too.
  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null));
  }, []);

  // On first load there's no access token in memory yet (it's never persisted
  // client-side) — try the httpOnly refresh cookie to silently restore a session.
  useEffect(() => {
    (async () => {
      try {
        const tokens = await authService.refresh();
        setApiAccessToken(tokens.access_token);
        const me = await authService.getProfile();
        setUser(me);
      } catch {
        setApiAccessToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (payload) => {
    const tokens = await authService.login(payload);
    setApiAccessToken(tokens.access_token);
    const me = await authService.getProfile();
    setUser(me);
  }, []);

  const register = useCallback(
    async (payload) => {
      await authService.register(payload);
      await login({ email: payload.email, password: payload.password });
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      setApiAccessToken(null);
      setUser(null);
    }
  }, []);

  const refreshProfile = useCallback(async () => {
    const me = await authService.getProfile();
    setUser(me);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isLoading, isAuthenticated: !!user, login, register, logout, refreshProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext must be used within an AuthProvider");
  return ctx;
}
