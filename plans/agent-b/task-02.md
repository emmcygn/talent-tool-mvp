# Agent B — Task 02: Layout Shells + Auth Flow

## Mission
Create the root layout with providers, Mind layout (minimal top nav), Mothership layout (sidebar + copilot panel), demo login page with one-click persona buttons, and auth guard middleware routing users by role.

## Context
Day 1, after Task 01. The Next.js project is scaffolded, shadcn/ui installed, Supabase client configured. This task builds the app shell that every subsequent page lives inside. The demo login page is the entry point — no registration flow, just pre-seeded user buttons.

## Prerequisites
- Agent B Task 01 complete (Next.js scaffold, shadcn/ui, Supabase client, utils)
- Agent A Task 01 complete (pre-seeded users exist in Supabase — or will exist; build against known user shapes)

## Checklist
- [ ] Create root layout (`app/layout.tsx`) with Supabase provider, theme provider, Toaster
- [ ] Create `app/providers.tsx` — client component wrapping Supabase + theme context
- [ ] Create `app/page.tsx` — redirects to `/login` or appropriate dashboard based on auth state
- [ ] Create `app/login/page.tsx` — demo login with one-click persona buttons
- [ ] Create `app/mind/layout.tsx` — minimal top nav layout for clients
- [ ] Create `app/mothership/layout.tsx` — sidebar nav + copilot panel for talent partners/admins
- [ ] Create `middleware.ts` — auth guard that routes by role
- [ ] Create `lib/auth.ts` — auth helper functions (sign in, sign out, get session, get user role)
- [ ] Verify: all layouts render, login flow works, middleware redirects correctly
- [ ] Commit: "Agent B Task 02: Layout shells + auth flow"

## Implementation Details

### Providers (`app/providers.tsx`)

```tsx
"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { createClient } from "@/lib/supabase";
import type { User } from "@/contracts/canonical";
import type { SupabaseClient } from "@supabase/supabase-js";

interface AuthContextValue {
  supabase: SupabaseClient;
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function Providers({ children }: { children: ReactNode }) {
  const [supabase] = useState(() => createClient());
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (session?.user) {
          // Fetch full user profile from our users table
          const { data } = await supabase
            .from("users")
            .select("*")
            .eq("id", session.user.id)
            .single();
          setUser(data as User | null);
        } else {
          setUser(null);
        }
        setLoading(false);
      }
    );
    return () => subscription.unsubscribe();
  }, [supabase]);

  const signOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ supabase, user, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### Root Layout (`app/layout.tsx`)

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "./providers";
import { Toaster } from "@/components/ui/toaster";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RecruitTech",
  description: "AI-powered recruitment platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased bg-background text-foreground`}>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
```

### Landing Page (`app/page.tsx`)

```tsx
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase";

export default function HomePage() {
  // Root page always redirects — middleware handles auth routing
  redirect("/login");
}
```

### Auth Helpers (`lib/auth.ts`)

```typescript
import { createClient } from "@/lib/supabase";
import type { UserRole } from "@/contracts/canonical";

// Pre-seeded demo users — these match Agent A's seed data
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
```

### Demo Login Page (`app/login/page.tsx`)

```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Briefcase, Shield, Loader2 } from "lucide-react";
import { signInAsDemo, getDashboardPath, DEMO_USERS } from "@/lib/auth";
import type { UserRole } from "@/contracts/canonical";

const PERSONA_ICONS = {
  talent_partner: Users,
  client: Briefcase,
  admin: Shield,
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
            RecruitTech
          </h1>
          <p className="text-lg text-slate-500">
            AI-powered recruitment platform demo
          </p>
        </div>

        {/* Persona Cards */}
        <div className="grid gap-4">
          {(Object.entries(DEMO_USERS) as [UserRole, typeof DEMO_USERS[UserRole]][]).map(
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

        {/* Footer */}
        <p className="text-center text-sm text-slate-400">
          Demo accounts with pre-loaded data. No registration required.
        </p>
      </div>
    </div>
  );
}
```

### Mind Layout (`app/mind/layout.tsx`)

Navigation items for Mind (client-facing):
- Dashboard (`/mind/dashboard`) — LayoutDashboard icon
- My Roles (`/mind/roles`) — Briefcase icon
- Candidates (`/mind/candidates`) — Users icon
- Quotes (`/mind/quotes`) — Receipt icon
- Pipeline (`/mind/pipeline`) — Kanban icon

```tsx
"use client";

import { type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  LayoutDashboard,
  Briefcase,
  Users,
  Receipt,
  KanbanSquare,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/app/providers";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/mind/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/mind/roles", label: "My Roles", icon: Briefcase },
  { href: "/mind/candidates", label: "Candidates", icon: Users },
  { href: "/mind/quotes", label: "Quotes", icon: Receipt },
  { href: "/mind/pipeline", label: "Pipeline", icon: KanbanSquare },
];

export default function MindLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-white">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 border-b border-slate-100 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          {/* Logo */}
          <Link href="/mind/dashboard" className="text-xl font-semibold text-slate-900">
            Mind
          </Link>

          {/* Nav Links */}
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={cn(
                      "gap-2 text-slate-500 hover:text-slate-900",
                      isActive && "bg-slate-100 text-slate-900"
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </nav>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-2">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="bg-slate-100 text-xs">
                    {user?.full_name?.charAt(0) ?? "U"}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm text-slate-700">{user?.full_name ?? "User"}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={signOut} className="gap-2 text-red-600">
                <LogOut className="h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Page Content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        {children}
      </main>
    </div>
  );
}
```

### Mothership Layout (`app/mothership/layout.tsx`)

Sidebar navigation items for Mothership:
- **Main section:**
  - Dashboard (`/mothership/dashboard`) — LayoutDashboard
  - Candidates (`/mothership/candidates`) — Users
  - Matching (`/mothership/matching`) — Sparkles
  - Collections (`/mothership/collections`) — FolderOpen
  - Handoffs (`/mothership/handoffs`) — ArrowRightLeft
  - Copilot (`/mothership/copilot`) — MessageSquare
- **Admin section (collapsible, visible to admin role only):**
  - Analytics (`/mothership/admin/analytics`) — BarChart3
  - Data Quality (`/mothership/admin/quality`) — ShieldCheck
  - Adapters (`/mothership/admin/adapters`) — Plug
  - Users (`/mothership/admin/users`) — UserCog

```tsx
"use client";

import { type ReactNode, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard,
  Users,
  Sparkles,
  FolderOpen,
  ArrowRightLeft,
  MessageSquare,
  BarChart3,
  ShieldCheck,
  Plug,
  UserCog,
  ChevronDown,
  ChevronRight,
  PanelRightOpen,
  PanelRightClose,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/app/providers";
import { cn } from "@/lib/utils";

const MAIN_NAV = [
  { href: "/mothership/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/mothership/candidates", label: "Candidates", icon: Users },
  { href: "/mothership/matching", label: "Matching", icon: Sparkles },
  { href: "/mothership/collections", label: "Collections", icon: FolderOpen },
  { href: "/mothership/handoffs", label: "Handoffs", icon: ArrowRightLeft },
  { href: "/mothership/copilot", label: "Copilot", icon: MessageSquare },
];

const ADMIN_NAV = [
  { href: "/mothership/admin/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/mothership/admin/quality", label: "Data Quality", icon: ShieldCheck },
  { href: "/mothership/admin/adapters", label: "Adapters", icon: Plug },
  { href: "/mothership/admin/users", label: "Users", icon: UserCog },
];

interface SidebarLinkProps {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  isActive: boolean;
}

function SidebarLink({ href, label, icon: Icon, isActive }: SidebarLinkProps) {
  return (
    <Link href={href}>
      <div
        className={cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          isActive
            ? "bg-slate-100 text-slate-900"
            : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
        )}
      >
        <Icon className="h-4 w-4 shrink-0" />
        {label}
      </div>
    </Link>
  );
}

export default function MothershipLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [adminExpanded, setAdminExpanded] = useState(
    pathname.startsWith("/mothership/admin")
  );
  const [copilotOpen, setCopilotOpen] = useState(false);

  const isAdmin = user?.role === "admin";

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
        {/* Logo */}
        <div className="flex h-16 items-center px-6">
          <Link href="/mothership/dashboard" className="text-xl font-semibold text-slate-900">
            Mothership
          </Link>
        </div>

        {/* Main Nav */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
          {MAIN_NAV.map((item) => (
            <SidebarLink
              key={item.href}
              {...item}
              isActive={pathname.startsWith(item.href)}
            />
          ))}

          {/* Admin Section (collapsible) */}
          {isAdmin && (
            <>
              <Separator className="my-3" />
              <button
                onClick={() => setAdminExpanded(!adminExpanded)}
                className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400 hover:text-slate-600"
              >
                {adminExpanded ? (
                  <ChevronDown className="h-3 w-3" />
                ) : (
                  <ChevronRight className="h-3 w-3" />
                )}
                Admin
              </button>
              {adminExpanded &&
                ADMIN_NAV.map((item) => (
                  <SidebarLink
                    key={item.href}
                    {...item}
                    isActive={pathname.startsWith(item.href)}
                  />
                ))}
            </>
          )}
        </nav>

        {/* User Footer */}
        <div className="border-t border-slate-200 p-3">
          <div className="flex items-center gap-3 rounded-md px-3 py-2">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-slate-100 text-xs">
                {user?.full_name?.charAt(0) ?? "U"}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium text-slate-900">
                {user?.full_name ?? "User"}
              </p>
              <p className="truncate text-xs text-slate-500 capitalize">
                {user?.role?.replace("_", " ") ?? ""}
              </p>
            </div>
            <Button variant="ghost" size="icon" onClick={signOut} className="h-8 w-8">
              <LogOut className="h-4 w-4 text-slate-400" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
          <div /> {/* Left slot — page title injected by child */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCopilotOpen(!copilotOpen)}
            className="gap-2 text-slate-500"
          >
            {copilotOpen ? (
              <PanelRightClose className="h-4 w-4" />
            ) : (
              <PanelRightOpen className="h-4 w-4" />
            )}
            Copilot
          </Button>
        </header>

        {/* Content + Copilot Panel */}
        <div className="flex flex-1 overflow-hidden">
          {/* Page Content */}
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>

          {/* Copilot Sidebar Panel */}
          {copilotOpen && (
            <aside className="w-96 shrink-0 border-l border-slate-200 bg-white">
              {/* Copilot component will be built in Task 12 */}
              <div className="flex h-full items-center justify-center text-sm text-slate-400">
                Copilot panel — Task 12
              </div>
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
```

### Auth Middleware (`middleware.ts`)

```typescript
import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public routes — no auth required
  if (pathname === "/" || pathname === "/login") {
    return NextResponse.next();
  }

  let response = NextResponse.next({
    request: { headers: request.headers },
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            request.cookies.set(name, value);
            response.cookies.set(name, value, options);
          });
        },
      },
    }
  );

  const { data: { session } } = await supabase.auth.getSession();

  // No session — redirect to login
  if (!session) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Fetch user role from users table
  const { data: user } = await supabase
    .from("users")
    .select("role")
    .eq("id", session.user.id)
    .single();

  const role = user?.role as string | undefined;

  // Route guards — enforce product boundaries
  if (pathname.startsWith("/mind") && role !== "client") {
    // Non-clients trying to access Mind — redirect to their dashboard
    if (role === "talent_partner") {
      return NextResponse.redirect(new URL("/mothership/dashboard", request.url));
    }
    if (role === "admin") {
      return NextResponse.redirect(new URL("/mothership/admin/analytics", request.url));
    }
  }

  if (pathname.startsWith("/mothership") && role === "client") {
    // Clients trying to access Mothership — redirect to Mind
    return NextResponse.redirect(new URL("/mind/dashboard", request.url));
  }

  if (pathname.startsWith("/mothership/admin") && role !== "admin") {
    // Non-admins trying to access admin — redirect to mothership dashboard
    return NextResponse.redirect(new URL("/mothership/dashboard", request.url));
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api).*)",
  ],
};
```

## Outputs
- `app/layout.tsx` — root layout with providers and Toaster
- `app/providers.tsx` — AuthContext with Supabase session management
- `app/page.tsx` — landing redirect
- `app/login/page.tsx` — demo login with persona buttons
- `app/mind/layout.tsx` — minimal top nav shell for clients
- `app/mothership/layout.tsx` — sidebar nav + copilot panel for talent partners/admins
- `middleware.ts` — auth guard with role-based routing
- `lib/auth.ts` — auth helpers and demo user config

## Acceptance Criteria
1. `npm run build` passes with no errors
2. Visiting `/` redirects to `/login`
3. Login page shows three persona cards — Talent Partner, Client, Admin
4. Clicking a persona button signs in and redirects to the correct dashboard path
5. Mind layout shows a clean top navigation bar with 5 nav items
6. Mothership layout shows a sidebar with 6 main nav items + collapsible admin section (4 items)
7. Copilot panel toggles open/closed in Mothership layout
8. Middleware redirects unauthenticated users to `/login`
9. Middleware prevents clients from accessing `/mothership/*` and vice versa
10. Middleware prevents non-admins from accessing `/mothership/admin/*`

## Handoff Notes
- **To Agent A:** Demo user credentials are defined in `lib/auth.ts`. Seed users must match these emails and passwords exactly: `alex.morgan@mothership.demo` / `demo-talent-2026` (talent_partner), `jamie.chen@acmecorp.demo` / `demo-client-2026` (client), `sam.patel@mothership.demo` / `demo-admin-2026` (admin). Note this in HANDOFF.md.
- **To Task 03:** Both layouts are functional. Mind has a `max-w-7xl` content area. Mothership has a sidebar + main content + optional copilot panel. All pages will render inside these shells.
- **To Task 12:** The Mothership layout has a copilot sidebar placeholder (`w-96`, toggled by button in top bar). Replace the placeholder div with the real copilot component.
- **Decision:** Using Supabase `onAuthStateChange` for client-side auth state. Middleware handles server-side route protection. No theme toggle yet — light mode only; dark mode in Task 16.
