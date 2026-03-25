"use client";

import { type ReactNode, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
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
  Menu,
  X,
} from "lucide-react";
import { useAuth } from "@/app/providers";
import { CopilotSidebar } from "@/components/mothership/copilot-sidebar";
import { cn } from "@/lib/utils";
import { useKeyboardShortcuts } from "@/lib/use-keyboard-shortcuts";

const MAIN_NAV = [
  { href: "/mothership/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/mothership/candidates/new", label: "Candidates", icon: Users },
  { href: "/mothership/matching", label: "Matching", icon: Sparkles },
  { href: "/mothership/collections", label: "Collections", icon: FolderOpen },
  { href: "/mothership/handoffs", label: "Handoffs", icon: ArrowRightLeft },
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
  onClick?: () => void;
}

function SidebarLink({ href, label, icon: Icon, isActive, onClick }: SidebarLinkProps) {
  return (
    <Link href={href} onClick={onClick}>
      <div
        className={cn(
          "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
          isActive
            ? "bg-primary/10 text-primary"
            : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
        )}
      >
        <Icon className="h-4 w-4 shrink-0" />
        {label}
      </div>
    </Link>
  );
}

function SidebarContent({
  pathname,
  user,
  isAdmin,
  adminExpanded,
  setAdminExpanded,
  signOut,
  onNavClick,
}: {
  pathname: string;
  user: ReturnType<typeof useAuth>["user"];
  isAdmin: boolean;
  adminExpanded: boolean;
  setAdminExpanded: (v: boolean) => void;
  signOut: () => void;
  onNavClick?: () => void;
}) {
  return (
    <>
      {/* Brand */}
      <div className="flex h-16 items-center px-6 border-b border-white/6">
        <Link href="/mothership/dashboard" className="flex items-center gap-2" onClick={onNavClick}>
          <div className="h-7 w-7 rounded-lg teal-gradient flex items-center justify-center">
            <span className="text-xs font-bold text-primary-foreground">M</span>
          </div>
          <span className="text-lg font-semibold text-foreground tracking-tight">Mothership</span>
        </Link>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {MAIN_NAV.map((item) => (
          <SidebarLink
            key={item.href}
            {...item}
            isActive={pathname.startsWith(item.href)}
            onClick={onNavClick}
          />
        ))}

        {isAdmin && (
          <>
            <div className="my-4 h-px bg-white/6" />
            <button
              onClick={() => setAdminExpanded(!adminExpanded)}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/60 hover:text-muted-foreground transition-colors"
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
                  onClick={onNavClick}
                />
              ))}
          </>
        )}
      </nav>

      {/* User */}
      <div className="border-t border-white/6 p-3">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2.5">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
              {user?.first_name?.charAt(0) ?? "U"}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-foreground">
              {user ? `${user.first_name} ${user.last_name}` : "User"}
            </p>
            <p className="truncate text-xs text-muted-foreground capitalize">
              {user?.role?.replace("_", " ") ?? ""}
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={signOut} className="h-8 w-8 text-muted-foreground hover:text-foreground">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </>
  );
}

export default function MothershipLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [adminExpanded, setAdminExpanded] = useState(
    pathname.startsWith("/mothership/admin")
  );
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useKeyboardShortcuts();
  const isAdmin = user?.role === "admin";

  return (
    <div className="flex h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-white/6 bg-sidebar">
        <SidebarContent
          pathname={pathname}
          user={user}
          isAdmin={isAdmin}
          adminExpanded={adminExpanded}
          setAdminExpanded={setAdminExpanded}
          signOut={signOut}
        />
      </aside>

      {/* Mobile Sidebar Sheet */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent side="left" className="w-64 p-0 bg-sidebar border-white/6">
          <SidebarContent
            pathname={pathname}
            user={user}
            isAdmin={isAdmin}
            adminExpanded={adminExpanded}
            setAdminExpanded={setAdminExpanded}
            signOut={signOut}
            onNavClick={() => setMobileMenuOpen(false)}
          />
        </SheetContent>
      </Sheet>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/6 bg-background/80 backdrop-blur-sm px-4 md:px-6">
          {/* Mobile hamburger */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden h-9 w-9 text-muted-foreground"
            onClick={() => setMobileMenuOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="hidden md:block" />

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCopilotOpen(!copilotOpen)}
            className={cn(
              "gap-2 text-sm transition-all",
              copilotOpen
                ? "text-primary bg-primary/10"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {copilotOpen ? (
              <PanelRightClose className="h-4 w-4" />
            ) : (
              <PanelRightOpen className="h-4 w-4" />
            )}
            <MessageSquare className="h-4 w-4" />
            <span className="hidden sm:inline">Copilot</span>
          </Button>
        </header>

        <div className="flex flex-1 overflow-hidden">
          <main className="flex-1 overflow-y-auto p-4 md:p-6">
            {children}
          </main>

          {/* Copilot: full-screen overlay on mobile, side panel on desktop */}
          {copilotOpen && (
            <>
              {/* Mobile: full-screen overlay */}
              <div className="fixed inset-0 z-50 bg-card flex flex-col md:hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-white/6 shrink-0">
                  <span className="text-sm font-semibold">Copilot</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setCopilotOpen(false)}
                    className="h-8 w-8"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex-1 overflow-hidden">
                  <CopilotSidebar pageContext={
                    pathname.includes("/matching") ? "matching"
                    : pathname.includes("/collections") ? "collections"
                    : pathname.includes("/admin") ? "admin"
                    : "default"
                  } />
                </div>
              </div>

              {/* Desktop: side panel */}
              <div className="hidden md:block">
                <CopilotSidebar pageContext={
                  pathname.includes("/matching") ? "matching"
                  : pathname.includes("/collections") ? "collections"
                  : pathname.includes("/admin") ? "admin"
                  : "default"
                } />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
