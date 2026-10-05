import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

import {
  clearAccessToken,
  getAccessToken,
  storeAccessToken,
} from "../api/client";

interface AuthContextValue {
  accessToken: string | null;
  isAuthenticated: boolean;
  setAccessToken: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessTokenState] = useState<string | null>(
    getAccessToken,
  );

  function setAccessToken(token: string) {
    storeAccessToken(token);
    setAccessTokenState(token);
  }

  function logout() {
    clearAccessToken();
    setAccessTokenState(null);
  }

  return (
    <AuthContext.Provider
      value={{
        accessToken,
        isAuthenticated: accessToken !== null,
        setAccessToken,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}