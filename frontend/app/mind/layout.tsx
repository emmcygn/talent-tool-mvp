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
      <header className="sticky top-0 z-50 border-b border-slate-100 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/mind/dashboard" className="text-xl font-semibold text-slate-900">
            Mind
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

          <DropdownMenu>
            <DropdownMenuTrigger className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm hover:bg-accent focus:outline-none">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-slate-100 text-xs">
                  {user?.full_name?.charAt(0) ?? "U"}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm text-slate-700">{user?.full_name ?? "User"}</span>
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

      <main className="mx-auto max-w-7xl px-6 py-8">
        {children}
      </main>
    </div>
  );
}
