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
  useKeyboardShortcuts();

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-white/6 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/mind/dashboard" className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-blue-500/20 border border-blue-500/20 flex items-center justify-center">
              <span className="text-xs font-bold text-blue-400">M</span>
            </div>
            <span className="text-lg font-semibold text-foreground tracking-tight">Mind</span>
          </Link>

          <nav className="flex items-center gap-1">
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

          <DropdownMenu>
            <DropdownMenuTrigger className="inline-flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm hover:bg-white/5 transition-colors focus:outline-none">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-blue-500/10 text-blue-400 text-xs font-semibold">
                  {user?.first_name?.charAt(0) ?? "U"}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm text-muted-foreground">{user ? `${user.first_name} ${user.last_name}` : "User"}</span>
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

      <main className="mx-auto max-w-7xl px-6 py-8">
        {children}
      </main>
    </div>
  );
}
