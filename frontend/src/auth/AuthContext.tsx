import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

import {
  AUTH_UNAUTHORIZED_EVENT,
  type AuthUser,
  type RegisterPayload,
  clearAccessToken,
  getAccessToken,
  getMe,
  login as apiLogin,
  register as apiRegister,
  setAccessToken,
} from "@/services/api";

interface AuthContextValue {
  user: AuthUser | null;
  initializing: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [initializing, setInitializing] = useState(true);

  const handleUnauthorized = useCallback(() => {
    clearAccessToken();
    setUser(null);
  }, []);

  useEffect(() => {
    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);

    const token = getAccessToken();

    if (!token) {
      setInitializing(false);
      return;
    }

    getMe()
      .then(setUser)
      .catch(handleUnauthorized)
      .finally(() => setInitializing(false));

    return () =>
      window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
  }, [handleUnauthorized]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiLogin(email, password);
    setAccessToken(response.access_token);
    setUser(response.user);
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const response = await apiRegister(payload);
    setAccessToken(response.access_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    handleUnauthorized();
  }, [handleUnauthorized]);

  const value = useMemo(
    () => ({ user, initializing, login, register, logout }),
    [user, initializing, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
