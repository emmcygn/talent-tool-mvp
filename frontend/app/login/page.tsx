"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Briefcase, Shield, Loader2, Play } from "lucide-react";
import { signInAsDemo, getDashboardPath, DEMO_USERS } from "@/lib/auth";
import type { UserRole } from "@/contracts/canonical";
import { DemoOverlay } from "@/components/shared/demo-overlay";

const PERSONA_ICONS = {
  talent_partner: Users,
  client: Briefcase,
  admin: Shield,
} as const;

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState<UserRole | null>(null);
  const [showTour, setShowTour] = useState(false);

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="w-full max-w-2xl space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
            RecruitTech
          </h1>
          <p className="text-lg text-slate-500">
            AI-powered recruitment platform demo
          </p>
        </div>

        <div className="grid gap-4">
          {(Object.entries(DEMO_USERS) as [UserRole, (typeof DEMO_USERS)[UserRole]][]).map(
            ([role, config]) => {
              const Icon = PERSONA_ICONS[role];
              const isLoading = loading === role;
              return (
                <Card
                  key={role}
                  className="cursor-pointer transition-all hover:shadow-md hover:border-slate-300"
                  onClick={() => !loading && handleLogin(role)}
                >
                  <CardHeader className="flex flex-row items-center gap-4 pb-2">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100">
                      <Icon className="h-6 w-6 text-slate-700" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{config.label}</CardTitle>
                      <CardDescription>{config.description}</CardDescription>
                    </div>
                    <Button
                      variant="default"
                      disabled={!!loading}
                      className="min-w-[100px]"
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        "Sign in"
                      )}
                    </Button>
                  </CardHeader>
                </Card>
              );
            }
          )}
        </div>

        <div className="text-center space-y-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTour(true)}
            className="gap-2"
          >
            <Play className="h-4 w-4" />
            Take a Tour
          </Button>
          <p className="text-sm text-slate-400">
            Demo accounts with pre-loaded data. No registration required.
          </p>
        </div>

        {showTour && <DemoOverlay onClose={() => setShowTour(false)} />}
      </div>
    </div>
  );
}
