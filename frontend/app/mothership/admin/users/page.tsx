"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  UserCog, Plus, Search, Shield, Users, Briefcase,
} from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import { userFullName } from "@/contracts/canonical";
import type { User } from "@/contracts/canonical";

const roleBadgeStyle: Record<string, string> = {
  talent_partner: "bg-blue-50 text-blue-700 border-blue-200",
  client: "bg-green-50 text-green-700 border-green-200",
  admin: "bg-purple-50 text-purple-700 border-purple-200",
};

const roleIcon: Record<string, React.ElementType> = {
  talent_partner: Users,
  client: Briefcase,
  admin: Shield,
};

export default function UsersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.admin.users();
        setUsers(data);
      } catch {
        toast.error("Failed to load users");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = users.filter((u) => {
    const name = userFullName(u).toLowerCase();
    const q = searchQuery.toLowerCase();
    return name.includes(q) || u.email.toLowerCase().includes(q) || u.role.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <UserCog className="h-6 w-6" />
            User Management
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage platform users, roles, and access.
          </p>
        </div>
        <Button onClick={() => toast("Coming soon")}>
          <Plus className="h-4 w-4 mr-1.5" />
          Invite User
        </Button>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by name, email, or role..."
          className="pl-9"
        />
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="rounded-md border-0 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-slate-50">
                  <th className="text-left font-medium px-4 py-3">User</th>
                  <th className="text-left font-medium px-4 py-3">Email</th>
                  <th className="text-left font-medium px-4 py-3">Role</th>
                  <th className="text-left font-medium px-4 py-3">Joined</th>
                  <th className="text-right font-medium px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="px-4 py-3"><Skeleton className="h-5 w-32" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-5 w-40" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-5 w-24" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-5 w-20" /></td>
                      <td className="px-4 py-3 text-right"><Skeleton className="h-5 w-12 ml-auto" /></td>
                    </tr>
                  ))
                ) : (
                  <>
                    {filtered.map((user) => {
                      const RoleIcon = roleIcon[user.role] || Users;
                      return (
                        <tr key={user.id} className="border-b last:border-0 hover:bg-slate-50 transition-colors">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-3">
                              <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium text-slate-600">
                                {user.first_name[0]}{user.last_name[0]}
                              </div>
                              <span className="font-medium">{userFullName(user)}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">{user.email}</td>
                          <td className="px-4 py-3">
                            <Badge variant="outline" className={roleBadgeStyle[user.role] || ""}>
                              <RoleIcon className="h-3 w-3 mr-1" />
                              {user.role.replace("_", " ")}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {new Date(user.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <Button variant="ghost" size="sm">Edit</Button>
                          </td>
                        </tr>
                      );
                    })}
                    {filtered.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                          No users found matching your search.
                        </td>
                      </tr>
                    )}
                  </>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
