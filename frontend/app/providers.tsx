"use client";

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import { createClient } from "@/lib/supabase";
import type { User } from "@/contracts/canonical";
import type { SupabaseClient } from "@supabase/supabase-js";

interface AuthContextValue {
  supabase: SupabaseClient;
  user: User | null;
  loading: boolean;
  setDemoUser: (user: User) => void;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

const DEMO_USER_KEY = "recruittech_demo_user";

export function Providers({ children }: { children: ReactNode }) {
  const [supabase] = useState(() => createClient());
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore demo user from sessionStorage on mount
  useEffect(() => {
    const stored = sessionStorage.getItem(DEMO_USER_KEY);
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        sessionStorage.removeItem(DEMO_USER_KEY);
      }
    }
  }, []);

  // Listen for real Supabase auth changes
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        if (session?.user) {
          try {
            const { data } = await supabase
              .from("users")
              .select("*")
              .eq("id", session.user.id)
              .single();
            if (data) {
              setUser(data as User);
              sessionStorage.removeItem(DEMO_USER_KEY);
            }
          } catch {
            // If DB query fails, use JWT metadata
            const meta = session.user.user_metadata;
            setUser({
              id: session.user.id,
              email: session.user.email ?? "",
              first_name: session.user.email?.split("@")[0]?.split(".")[0] ?? "User",
              last_name: session.user.email?.split("@")[0]?.split(".")[1] ?? "",
              role: meta?.role ?? "talent_partner",
              organisation_id: null,
              is_active: true,
              created_at: session.user.created_at,
              updated_at: session.user.created_at,
            } as User);
          }
        } else if (!sessionStorage.getItem(DEMO_USER_KEY)) {
          setUser(null);
        }
        setLoading(false);
      }
    );
    // If no auth event fires within 2s, stop loading
    const timeout = setTimeout(() => setLoading(false), 2000);
    return () => {
      subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, [supabase]);

  const setDemoUser = useCallback((demoUser: User) => {
    setUser(demoUser);
    sessionStorage.setItem(DEMO_USER_KEY, JSON.stringify(demoUser));
    // Set cookie for middleware/proxy to read
    document.cookie = `recruittech_demo_role=${demoUser.role}; path=/; max-age=86400; samesite=lax`;
    setLoading(false);
  }, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut().catch(() => {});
    sessionStorage.removeItem(DEMO_USER_KEY);
    document.cookie = "recruittech_demo_role=; path=/; max-age=0";
    setUser(null);
  }, [supabase]);

  return (
    <AuthContext.Provider value={{ supabase, user, loading, setDemoUser, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
