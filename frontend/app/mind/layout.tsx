"use client";

import { type ReactNode, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Sheet, SheetContent } from "@/components/ui/sheet";
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
  Menu,
} from "lucide-react";
import { useAuth } from "@/app/providers";
import { cn } from "@/lib/utils";
import { useKeyboardShortcuts } from "@/lib/use-keyboard-shortcuts";

const NAV_ITEMS = [
  { href: "/mind/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/mind/roles/new", label: "Post Role", icon: Briefcase },
  { href: "/mind/candidates", label: "Candidates", icon: Users },
  { href: "/mind/quotes", label: "Quotes", icon: Receipt },
  { href: "/mind/pipeline", label: "Pipeline", icon: KanbanSquare },
];

export default function MindLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  useKeyboardShortcuts();

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-white/6 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-6">
          {/* Brand + Mobile hamburger */}
          <div className="flex items-center gap-3">
            {/* Mobile hamburger */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden h-9 w-9 text-muted-foreground"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>

            <Link href="/mind/dashboard" className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-lg bg-blue-500/20 border border-blue-500/20 flex items-center justify-center">
                <span className="text-xs font-bold text-blue-400">M</span>
              </div>
              <span className="text-lg font-semibold text-foreground tracking-tight">Mind</span>
            </Link>
          </div>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={cn(
                      "gap-2 text-muted-foreground hover:text-foreground transition-all",
                      isActive && "bg-white/8 text-foreground"
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </nav>

          {/* User dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger className="inline-flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm hover:bg-white/5 transition-colors focus:outline-none">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-blue-500/10 text-blue-400 text-xs font-semibold">
                  {user?.first_name?.charAt(0) ?? "U"}
                </AvatarFallback>
              </Avatar>
              <span className="hidden sm:inline text-sm text-muted-foreground">{user ? `${user.first_name} ${user.last_name}` : "User"}</span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-card border-white/8">
              <DropdownMenuItem onClick={signOut} className="gap-2 text-red-400 focus:text-red-400">
                <LogOut className="h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Mobile nav drawer */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent side="left" className="w-64 p-0 bg-background border-white/6">
          <div className="flex h-16 items-center px-6 border-b border-white/6">
            <Link href="/mind/dashboard" className="flex items-center gap-2" onClick={() => setMobileMenuOpen(false)}>
              <div className="h-7 w-7 rounded-lg bg-blue-500/20 border border-blue-500/20 flex items-center justify-center">
                <span className="text-xs font-bold text-blue-400">M</span>
              </div>
              <span className="text-lg font-semibold text-foreground tracking-tight">Mind</span>
            </Link>
          </div>
          <nav className="flex flex-col gap-1 px-3 py-4">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <div
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      isActive
                        ? "bg-blue-500/10 text-blue-400"
                        : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                    )}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {item.label}
                  </div>
                </Link>
              );
            })}
          </nav>
        </SheetContent>
      </Sheet>

      <main className="mx-auto max-w-7xl px-4 md:px-6 py-6 md:py-8">
        {children}
      </main>
    </div>
  );
}
