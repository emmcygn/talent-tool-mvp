import { createClient } from "@/lib/supabase";
import type { UserRole } from "@/contracts/canonical";

// Credentials aligned to backend seed data (backend/seed/users.py)
export const DEMO_USERS = {
  talent_partner: {
    email: "sarah.chen@recruittech.demo",
    password: "demo-partner-1",
    label: "Sarah Chen — Talent Partner",
    description: "Ingest candidates, run matching, manage collections, use copilot",
    icon: "Users",
  },
  client: {
    email: "alex.thompson@monzo.demo",
    password: "demo-client-1",
    label: "Alex Thompson — Hiring Manager (Monzo)",
    description: "Post roles, review matched candidates, request introductions",
    icon: "Briefcase",
  },
  admin: {
    email: "admin@recruittech.demo",
    password: "demo-admin-1",
    label: "Admin",
    description: "Platform analytics, data quality, adapter management",
    icon: "Shield",
  },
} as const;

export async function signInAsDemo(role: UserRole) {
  const supabase = createClient();
  const creds = DEMO_USERS[role];
  const { data, error } = await supabase.auth.signInWithPassword({
    email: creds.email,
    password: creds.password,
  });
  if (error) throw error;
  return data;
}

export function getDashboardPath(role: UserRole): string {
  switch (role) {
    case "talent_partner":
      return "/mothership/dashboard";
    case "client":
      return "/mind/dashboard";
    case "admin":
      return "/mothership/admin/analytics";
    default:
      return "/login";
  }
}
