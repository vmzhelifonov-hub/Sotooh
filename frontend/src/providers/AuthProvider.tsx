import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useMemo, type ReactNode } from "react";
import { authApi, type User } from "../api/endpoints";
import { useToast } from "./ToastProvider";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  refetch: () => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: false,
  refetch: () => undefined,
  logout: async () => undefined,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    retry: false,
  });
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const value = useMemo<AuthContextValue>(
    () => ({
      user: data ?? null,
      isLoading,
      refetch: () => void refetch(),
      logout: async () => {
        await authApi.logout();
        queryClient.clear();
        toast({ kind: "success", message: "ok" });
        window.location.href = "/login";
      },
    }),
    [data, isLoading, refetch, queryClient, toast]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
