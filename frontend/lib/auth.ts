import { createClient } from "@/lib/supabase";
import type { UserRole, User } from "@/contracts/canonical";

export const DEMO_USERS: Record<UserRole, {
  email: string;
  password: string;
  label: string;
  description: string;
  icon: string;
  mockUser: User;
}> = {
  talent_partner: {
    email: "sarah.chen@recruittech.demo",
    password: "demo-partner-1",
    label: "Sarah Chen — Talent Partner",
    description: "Ingest candidates, run matching, manage collections, use copilot",
    icon: "Users",
    mockUser: {
      id: "11111111-1111-1111-1111-111111111111",
      email: "sarah.chen@recruittech.demo",
      first_name: "Sarah",
      last_name: "Chen",
      role: "talent_partner",
      organisation_id: null,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  },
  client: {
    email: "alex.thompson@monzo.demo",
    password: "demo-client-1",
    label: "Alex Thompson — Hiring Manager (Monzo)",
    description: "Post roles, review matched candidates, request introductions",
    icon: "Briefcase",
    mockUser: {
      id: "22222222-2222-2222-2222-111111111111",
      email: "alex.thompson@monzo.demo",
      first_name: "Alex",
      last_name: "Thompson",
      role: "client",
      organisation_id: "aaaa0001-0001-0001-0001-000000000001",
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  },
  admin: {
    email: "admin@recruittech.demo",
    password: "demo-admin-1",
    label: "Admin",
    description: "Platform analytics, data quality, adapter management",
    icon: "Shield",
    mockUser: {
      id: "33333333-3333-3333-3333-111111111111",
      email: "admin@recruittech.demo",
      first_name: "Admin",
      last_name: "User",
      role: "admin",
      organisation_id: null,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  },
};

export type DemoSignInResult =
  | { type: "supabase"; data: unknown }
  | { type: "demo"; user: User };

export async function signInAsDemo(role: UserRole): Promise<DemoSignInResult> {
  const creds = DEMO_USERS[role];

  // Try real Supabase auth first
  try {
    const supabase = createClient();
    const { data, error } = await supabase.auth.signInWithPassword({
      email: creds.email,
      password: creds.password,
    });
    if (!error && data.user) {
      return { type: "supabase", data };
    }
  } catch {
    // Fall through to demo mode
  }

  // Fallback: demo mode bypass (no real auth)
  console.log(`[Demo Mode] Signing in as ${role} — Supabase auth unavailable, using mock user`);
  return { type: "demo", user: creds.mockUser };
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
