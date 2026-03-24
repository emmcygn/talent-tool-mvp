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
        <div className="flex h-16 items-center px-6">
          <Link href="/mothership/dashboard" className="text-xl font-semibold text-slate-900">
            Mothership
          </Link>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
          {MAIN_NAV.map((item) => (
            <SidebarLink
              key={item.href}
              {...item}
              isActive={pathname.startsWith(item.href)}
            />
          ))}

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
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
          <div />
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

        <div className="flex flex-1 overflow-hidden">
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>

          {copilotOpen && (
            <aside className="w-96 shrink-0 border-l border-slate-200 bg-white">
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
