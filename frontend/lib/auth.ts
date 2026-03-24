import { createClient } from "@/lib/supabase";
import type { UserRole } from "@/contracts/canonical";

export const DEMO_USERS = {
  talent_partner: {
    email: "alex.morgan@mothership.demo",
    password: "demo-talent-2026",
    label: "Talent Partner",
    description: "Ingest candidates, run matching, manage collections, use copilot",
    icon: "Users",
  },
  client: {
    email: "jamie.chen@acmecorp.demo",
    password: "demo-client-2026",
    label: "Client / Hiring Manager",
    description: "Post roles, review matched candidates, request introductions",
    icon: "Briefcase",
  },
  admin: {
    email: "sam.patel@mothership.demo",
    password: "demo-admin-2026",
    label: "Admin / Ops",
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
