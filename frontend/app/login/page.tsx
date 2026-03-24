"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Users, Briefcase, Shield, Loader2, ArrowRight, Sparkles } from "lucide-react";
import { signInAsDemo, getDashboardPath, DEMO_USERS } from "@/lib/auth";
import type { UserRole } from "@/contracts/canonical";

const PERSONA_CONFIG = {
  talent_partner: {
    icon: Users,
    gradient: "from-teal-500/20 to-emerald-500/20",
    border: "hover:border-teal-500/30",
    iconColor: "text-teal-400",
    tag: "Internal",
  },
  client: {
    icon: Briefcase,
    gradient: "from-blue-500/20 to-cyan-500/20",
    border: "hover:border-blue-500/30",
    iconColor: "text-blue-400",
    tag: "External",
  },
  admin: {
    icon: Shield,
    gradient: "from-purple-500/20 to-violet-500/20",
    border: "hover:border-purple-500/30",
    iconColor: "text-purple-400",
    tag: "Admin",
  },
} as const;

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState<UserRole | null>(null);

  const handleLogin = async (role: UserRole) => {
    setLoading(role);
    try {
      await signInAsDemo(role);
      router.push(getDashboardPath(role));
    } catch (err) {
      console.error("Login failed:", err);
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-mesh bg-grid">
      {/* Ambient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-teal-500/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-blue-500/5 blur-[100px] pointer-events-none" />

      <div className="w-full max-w-lg space-y-10 px-6 relative z-10">
        {/* Brand */}
        <div className="text-center space-y-4" style={{ animation: "fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-xs text-muted-foreground tracking-wider uppercase">
            <Sparkles className="h-3 w-3 text-primary" />
            AI-Powered Platform
          </div>
          <h1 className="text-5xl font-bold tracking-tight">
            <span className="teal-gradient-text">Recruit</span>
            <span className="text-foreground">Tech</span>
          </h1>
          <p className="text-muted-foreground text-lg">
            Intelligent matching. Unified pipeline. Smarter placements.
          </p>
        </div>

        {/* Persona Cards */}
        <div className="grid gap-3" style={{ animation: "fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both" }}>
          {(Object.entries(DEMO_USERS) as [UserRole, (typeof DEMO_USERS)[UserRole]][]).map(
            ([role, config], index) => {
              const persona = PERSONA_CONFIG[role];
              const Icon = persona.icon;
              const isLoading = loading === role;
              return (
                <button
                  key={role}
                  onClick={() => !loading && handleLogin(role)}
                  disabled={!!loading}
                  className={`group relative w-full text-left rounded-xl border border-white/8 bg-card/60 backdrop-blur-sm p-5 transition-all duration-300 ${persona.border} hover:bg-card/80 hover:translate-y-[-1px] hover:shadow-lg hover:shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed`}
                  style={{ animationDelay: `${0.2 + index * 0.08}s` }}
                >
                  <div className={`absolute inset-0 rounded-xl bg-gradient-to-r ${persona.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                  <div className="relative flex items-center gap-4">
                    <div className={`flex h-11 w-11 items-center justify-center rounded-lg bg-white/5 border border-white/8 ${persona.iconColor} transition-colors`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground">{config.label}</span>
                        <span className="text-[10px] uppercase tracking-widest text-muted-foreground px-2 py-0.5 rounded-full border border-white/8 bg-white/5">{persona.tag}</span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-0.5">{config.description}</p>
                    </div>
                    <div className="flex items-center">
                      {isLoading ? (
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      ) : (
                        <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
                      )}
                    </div>
                  </div>
                </button>
              );
            }
          )}
        </div>

        {/* Footer */}
        <div className="text-center" style={{ animation: "fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.4s both" }}>
          <p className="text-xs text-muted-foreground/60">
            Demo accounts with pre-loaded UK market data. No registration required.
          </p>
        </div>
      </div>
    </div>
  );
}
