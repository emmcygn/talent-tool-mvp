# Agent B — Task 15: Admin — Adapters + Monitoring + Users

## Mission
Build the adapter health page with status cards, schema mapping visualization, and sync controls. Build the AI pipeline monitoring view with extraction queue stats, confidence distribution, processing time charts, and LLM usage. Build the user management page with data table, role badges, and add/deactivate actions.

## Context
Day 6. These are the operational admin views — the "control room" for the platform. Adapter health shows how data is flowing in from external systems. AI pipeline monitoring shows the LLM extraction and matching engine performance. User management is straightforward CRUD. All views follow the Grafana-density / Vercel-cleanliness aesthetic.

## Prerequisites
- B-01: Next.js scaffold, TypeScript contracts, shadcn/ui installed
- B-04: API client
- B-14: Chart components (time-series, bar charts) already built
- A-15: Admin endpoints for adapter health, pipeline monitoring

## Checklist
- [ ] Create `AdapterStatusCard` component (`components/mothership/adapter-status-card.tsx`)
- [ ] Create `SchemaMapping` component — table showing adapter fields to canonical fields
- [ ] Create adapters page (`app/mothership/admin/adapters/page.tsx`)
- [ ] Create AI pipeline monitoring section with queue stats and charts
- [ ] Create `UserManagementTable` component
- [ ] Create users page (`app/mothership/admin/users/page.tsx`)
- [ ] Wire to API client with loading states
- [ ] Commit: "Agent B Task 15: Admin adapters + monitoring + users"

## Implementation Details

### Adapter Status Card (`components/mothership/adapter-status-card.tsx`)

```tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  RefreshCw, CheckCircle2, XCircle, AlertTriangle, Clock,
  Database, ArrowDownToLine,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

interface AdapterHealth {
  name: string;
  status: "healthy" | "warning" | "error" | "offline";
  lastSync: string;
  recordsIngested: number;
  recordsTotal: number;
  errors: number;
  dataQualityScore: number;
  icon: string; // Adapter logo identifier
}

interface AdapterStatusCardProps {
  adapter: AdapterHealth;
  onResync: () => void;
}

const statusConfig: Record<string, {
  label: string;
  color: string;
  icon: React.ElementType;
}> = {
  healthy: { label: "Healthy", color: "border-green-300 bg-green-50 text-green-700", icon: CheckCircle2 },
  warning: { label: "Warning", color: "border-amber-300 bg-amber-50 text-amber-700", icon: AlertTriangle },
  error: { label: "Error", color: "border-red-300 bg-red-50 text-red-700", icon: XCircle },
  offline: { label: "Offline", color: "border-slate-300 bg-slate-50 text-slate-500", icon: Clock },
};

const adapterIcons: Record<string, string> = {
  bullhorn: "BH",
  hubspot: "HS",
  linkedin: "LI",
};

export function AdapterStatusCard({ adapter, onResync }: AdapterStatusCardProps) {
  const status = statusConfig[adapter.status];
  const StatusIcon = status.icon;
  const qualityColor =
    adapter.dataQualityScore >= 90 ? "text-green-600" :
    adapter.dataQualityScore >= 70 ? "text-amber-600" : "text-red-600";

  return (
    <Card className="transition-all hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-900 text-white flex items-center justify-center text-sm font-bold">
              {adapterIcons[adapter.name.toLowerCase()] ?? adapter.name.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <CardTitle className="text-base">{adapter.name}</CardTitle>
              <div className="flex items-center gap-1 mt-0.5">
                <Clock className="h-3 w-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  Last sync {formatRelativeTime(adapter.lastSync)}
                </span>
              </div>
            </div>
          </div>
          <Badge variant="outline" className={status.color}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {status.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Records */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <div className="text-lg font-semibold">{adapter.recordsIngested.toLocaleString()}</div>
            <div className="text-[11px] text-muted-foreground">Records Synced</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-red-600">{adapter.errors}</div>
            <div className="text-[11px] text-muted-foreground">Errors</div>
          </div>
          <div>
            <div className={`text-lg font-semibold ${qualityColor}`}>
              {adapter.dataQualityScore}%
            </div>
            <div className="text-[11px] text-muted-foreground">Quality Score</div>
          </div>
        </div>

        {/* Progress bar */}
        <div>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-muted-foreground">Sync progress</span>
            <span className="font-medium">
              {adapter.recordsIngested}/{adapter.recordsTotal}
            </span>
          </div>
          <Progress
            value={(adapter.recordsIngested / adapter.recordsTotal) * 100}
            className="h-1.5"
          />
        </div>

        {/* Re-sync button */}
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={onResync}
        >
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Re-sync
        </Button>
      </CardContent>
    </Card>
  );
}

export type { AdapterHealth };
```

### Schema Mapping Table (`components/mothership/schema-mapping.tsx`)

```tsx
"use client";

import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";

interface SchemaField {
  adapterField: string;
  canonicalField: string;
  type: string;
  transform: string | null;
  required: boolean;
}

interface SchemaMappingProps {
  adapterName: string;
  fields: SchemaField[];
}

export function SchemaMapping({ adapterName, fields }: SchemaMappingProps) {
  return (
    <div className="rounded-md border overflow-hidden">
      <div className="bg-slate-50 px-4 py-2 border-b">
        <span className="text-sm font-medium">{adapterName} Field Mapping</span>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-white">
            <th className="text-left font-medium px-4 py-2 text-muted-foreground">
              Adapter Field
            </th>
            <th className="w-10"></th>
            <th className="text-left font-medium px-4 py-2 text-muted-foreground">
              Canonical Field
            </th>
            <th className="text-left font-medium px-4 py-2 text-muted-foreground">Type</th>
            <th className="text-left font-medium px-4 py-2 text-muted-foreground">Transform</th>
          </tr>
        </thead>
        <tbody>
          {fields.map((field) => (
            <tr key={field.adapterField} className="border-b last:border-0 hover:bg-slate-50/50">
              <td className="px-4 py-2 font-mono text-xs">{field.adapterField}</td>
              <td className="text-center">
                <ArrowRight className="h-3 w-3 text-muted-foreground inline" />
              </td>
              <td className="px-4 py-2 font-mono text-xs text-blue-700">{field.canonicalField}</td>
              <td className="px-4 py-2">
                <Badge variant="outline" className="text-[10px] py-0 font-mono">
                  {field.type}
                </Badge>
              </td>
              <td className="px-4 py-2 text-xs text-muted-foreground">
                {field.transform ?? "direct"}
                {field.required && (
                  <Badge variant="secondary" className="text-[10px] py-0 ml-1">req</Badge>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export type { SchemaField };
```

### Adapters Page (`app/mothership/admin/adapters/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { AdapterStatusCard, AdapterHealth } from "@/components/mothership/adapter-status-card";
import { SchemaMapping, SchemaField } from "@/components/mothership/schema-mapping";
import { MetricTile } from "@/components/shared/metric-tile";
import { TimeSeriesChart } from "@/components/charts/time-series-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Plug, Activity, Cpu, Brain, BarChart3, Clock, Zap, DollarSign,
  AlertTriangle, CheckCircle2,
} from "lucide-react";

// Mock schema mappings
const bullhornMapping: SchemaField[] = [
  { adapterField: "candidate.firstName", canonicalField: "first_name", type: "string", transform: null, required: true },
  { adapterField: "candidate.lastName", canonicalField: "last_name", type: "string", transform: null, required: true },
  { adapterField: "candidate.email", canonicalField: "email", type: "string", transform: "lowercase", required: false },
  { adapterField: "candidate.skills", canonicalField: "skills", type: "array", transform: "parse_csv", required: false },
  { adapterField: "candidate.salary", canonicalField: "salary_expectation", type: "SalaryRange", transform: "parse_range", required: false },
  { adapterField: "candidate.status", canonicalField: "availability", type: "enum", transform: "map_status", required: false },
];

export default function AdaptersPage() {
  const [adapters, setAdapters] = useState<AdapterHealth[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        // const data = await api.admin.adapterHealth();
        // setAdapters(data);
        // Mock data for now
        setAdapters([
          {
            name: "Bullhorn",
            status: "healthy",
            lastSync: new Date(Date.now() - 3600000).toISOString(),
            recordsIngested: 342,
            recordsTotal: 350,
            errors: 2,
            dataQualityScore: 94,
            icon: "bullhorn",
          },
          {
            name: "HubSpot",
            status: "warning",
            lastSync: new Date(Date.now() - 7200000).toISOString(),
            recordsIngested: 189,
            recordsTotal: 210,
            errors: 8,
            dataQualityScore: 78,
            icon: "hubspot",
          },
          {
            name: "LinkedIn",
            status: "healthy",
            lastSync: new Date(Date.now() - 1800000).toISOString(),
            recordsIngested: 156,
            recordsTotal: 156,
            errors: 0,
            dataQualityScore: 91,
            icon: "linkedin",
          },
        ]);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Mock AI pipeline data
  const extractionQueue = { pending: 12, processing: 3, completed: 847, failed: 5 };
  const processingTimeSeries = Array.from({ length: 24 }, (_, i) => ({
    date: `${i}:00`,
    value: Math.floor(Math.random() * 3000) + 500,
  }));

  return (
    <div className="p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Plug className="h-6 w-6" />
          Adapters &amp; Monitoring
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Integration health, schema mappings, and AI pipeline performance.
        </p>
      </div>

      <Tabs defaultValue="adapters" className="space-y-6">
        <TabsList>
          <TabsTrigger value="adapters">Adapter Health</TabsTrigger>
          <TabsTrigger value="schema">Schema Mapping</TabsTrigger>
          <TabsTrigger value="pipeline">AI Pipeline</TabsTrigger>
        </TabsList>

        {/* Adapter Health */}
        <TabsContent value="adapters">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-72 rounded-lg" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {adapters.map((adapter) => (
                <AdapterStatusCard
                  key={adapter.name}
                  adapter={adapter}
                  onResync={() => {
                    // Trigger re-sync via API
                  }}
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Schema Mapping */}
        <TabsContent value="schema" className="space-y-6">
          <SchemaMapping adapterName="Bullhorn" fields={bullhornMapping} />
          <SchemaMapping
            adapterName="HubSpot"
            fields={[
              { adapterField: "contact.firstname", canonicalField: "first_name", type: "string", transform: null, required: true },
              { adapterField: "contact.lastname", canonicalField: "last_name", type: "string", transform: null, required: true },
              { adapterField: "contact.email", canonicalField: "email", type: "string", transform: "lowercase", required: false },
              { adapterField: "contact.jobtitle", canonicalField: "experience[0].title", type: "string", transform: null, required: false },
              { adapterField: "contact.company", canonicalField: "experience[0].company", type: "string", transform: null, required: false },
            ]}
          />
          <SchemaMapping
            adapterName="LinkedIn"
            fields={[
              { adapterField: "profile.firstName", canonicalField: "first_name", type: "string", transform: null, required: true },
              { adapterField: "profile.lastName", canonicalField: "last_name", type: "string", transform: null, required: true },
              { adapterField: "profile.emailAddress", canonicalField: "email", type: "string", transform: "lowercase", required: false },
              { adapterField: "profile.positions", canonicalField: "experience", type: "array", transform: "map_positions", required: false },
              { adapterField: "profile.skills", canonicalField: "skills", type: "array", transform: "map_endorsements", required: false },
              { adapterField: "profile.publicProfileUrl", canonicalField: "linkedin_url", type: "string", transform: null, required: false },
            ]}
          />
        </TabsContent>

        {/* AI Pipeline Monitoring */}
        <TabsContent value="pipeline" className="space-y-6">
          {/* Queue stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricTile
              label="Pending"
              value={extractionQueue.pending}
              subtitle="In extraction queue"
              icon={<Clock className="h-4 w-4" />}
              loading={loading}
            />
            <MetricTile
              label="Processing"
              value={extractionQueue.processing}
              subtitle="Currently extracting"
              icon={<Cpu className="h-4 w-4" />}
              loading={loading}
            />
            <MetricTile
              label="Completed"
              value={extractionQueue.completed}
              subtitle="Total extracted"
              icon={<CheckCircle2 className="h-4 w-4" />}
              loading={loading}
            />
            <MetricTile
              label="Failed"
              value={extractionQueue.failed}
              subtitle="Needs review"
              icon={<AlertTriangle className="h-4 w-4" />}
              loading={loading}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Confidence distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Brain className="h-4 w-4" />
                  Extraction Confidence Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {[
                    { label: "High (> 0.9)", count: 612, pct: 72, color: "bg-green-500" },
                    { label: "Medium (0.7-0.9)", count: 178, pct: 21, color: "bg-amber-500" },
                    { label: "Low (< 0.7)", count: 57, pct: 7, color: "bg-red-500" },
                  ].map((bucket) => (
                    <div key={bucket.label}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span>{bucket.label}</span>
                        <span className="text-muted-foreground">
                          {bucket.count} ({bucket.pct}%)
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${bucket.color}`}
                          style={{ width: `${bucket.pct}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Processing time */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Processing Time (24h)
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-[200px] rounded-md" />
                ) : (
                  <TimeSeriesChart
                    data={processingTimeSeries}
                    color="#f59e0b"
                    height={200}
                  />
                )}
              </CardContent>
            </Card>
          </div>

          {/* LLM Usage */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                LLM Usage &amp; Cost
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">1.2M</div>
                  <div className="text-xs text-muted-foreground">Tokens (input)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">340k</div>
                  <div className="text-xs text-muted-foreground">Tokens (output)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">\u00a318.40</div>
                  <div className="text-xs text-muted-foreground">Estimated cost</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">GPT-4o</div>
                  <div className="text-xs text-muted-foreground">Model version</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### User Management Page (`app/mothership/admin/users/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { User, UserRole } from "@/contracts/canonical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  UserCog, Plus, Search, Shield, Users, Briefcase, MoreHorizontal,
} from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatDate } from "@/lib/utils";

const roleBadge: Record<UserRole, { label: string; className: string; icon: React.ElementType }> = {
  admin: { label: "Admin", className: "bg-purple-100 text-purple-700 border-purple-300", icon: Shield },
  talent_partner: { label: "Talent Partner", className: "bg-blue-100 text-blue-700 border-blue-300", icon: Users },
  client: { label: "Client", className: "bg-green-100 text-green-700 border-green-300", icon: Briefcase },
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newUser, setNewUser] = useState({ email: "", full_name: "", role: "talent_partner" as UserRole });

  useEffect(() => {
    async function load() {
      try {
        // const data = await api.admin.users();
        // setUsers(data);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = users.filter(
    (u) =>
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  function handleAddUser() {
    // Call API to create user
    setAddDialogOpen(false);
    setNewUser({ email: "", full_name: "", role: "talent_partner" });
  }

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <UserCog className="h-6 w-6" />
            User Management
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage talent partners, clients, and admin access.
          </p>
        </div>
        <Button onClick={() => setAddDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-1.5" />
          Add User
        </Button>
      </div>

      {/* Search */}
      <div className="relative mb-4 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search users..."
          className="pl-9"
        />
      </div>

      {/* User table */}
      <div className="rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-slate-50">
              <th className="text-left font-medium px-4 py-3">User</th>
              <th className="text-left font-medium px-4 py-3">Role</th>
              <th className="text-left font-medium px-4 py-3">Created</th>
              <th className="text-left font-medium px-4 py-3">Activity</th>
              <th className="w-10"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b">
                  <td className="px-4 py-3"><Skeleton className="h-8 w-48" /></td>
                  <td className="px-4 py-3"><Skeleton className="h-6 w-24" /></td>
                  <td className="px-4 py-3"><Skeleton className="h-4 w-20" /></td>
                  <td className="px-4 py-3"><Skeleton className="h-4 w-32" /></td>
                  <td></td>
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-muted-foreground">
                  {searchQuery ? "No users match your search." : "No users found."}
                </td>
              </tr>
            ) : (
              filtered.map((user) => {
                const role = roleBadge[user.role];
                const RoleIcon = role.icon;
                const initials = user.full_name.split(" ").map((n) => n[0]).join("").toUpperCase();

                return (
                  <tr key={user.id} className="border-b last:border-0 hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className="text-xs bg-slate-100">
                            {initials}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium">{user.full_name}</div>
                          <div className="text-xs text-muted-foreground">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className={role.className}>
                        <RoleIcon className="h-3 w-3 mr-1" />
                        {role.label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {/* Activity summary from signals */}
                      —
                    </td>
                    <td className="px-4 py-3">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>Edit role</DropdownMenuItem>
                          <DropdownMenuItem>View activity</DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">Deactivate</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Add User Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent className="sm:max-w-[420px]">
          <DialogHeader>
            <DialogTitle>Add User</DialogTitle>
            <DialogDescription>
              Invite a new user to the platform.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="user-name">Full Name</Label>
              <Input
                id="user-name"
                value={newUser.full_name}
                onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                placeholder="Jane Smith"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="user-email">Email</Label>
              <Input
                id="user-email"
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                placeholder="jane@company.com"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Role</Label>
              <Select
                value={newUser.role}
                onValueChange={(v) => setNewUser({ ...newUser, role: v as UserRole })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="talent_partner">Talent Partner</SelectItem>
                  <SelectItem value="client">Client</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleAddUser}
              disabled={!newUser.full_name.trim() || !newUser.email.trim()}
            >
              Add User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

## Outputs
- `frontend/components/mothership/adapter-status-card.tsx` — Adapter health card
- `frontend/components/mothership/schema-mapping.tsx` — Field mapping table
- `frontend/app/mothership/admin/adapters/page.tsx` — Adapters + AI pipeline page
- `frontend/app/mothership/admin/users/page.tsx` — User management page

## Acceptance Criteria
1. Adapter status cards show name, status badge, last sync time, records count, errors, and quality score
2. Re-sync button exists on each adapter card
3. Schema mapping tables show adapter fields mapped to canonical fields with types and transforms
4. AI pipeline monitoring shows extraction queue stats (pending/processing/completed/failed)
5. Confidence distribution renders as horizontal progress bars by bucket
6. Processing time chart renders using TimeSeriesChart component
7. LLM usage shows token counts and estimated cost
8. User management table is searchable, shows avatar, name, email, role badge, and created date
9. Add user dialog collects name, email, and role
10. Dropdown menu on each user row has edit, view activity, and deactivate options
11. Loading skeletons render for all sections

## Handoff Notes
- **To Agent A:** Frontend expects `GET /api/admin/adapters` returning array of adapter health objects. `POST /api/admin/adapters/{name}/resync` to trigger re-sync. `GET /api/admin/pipeline/stats` for extraction queue and LLM usage. `GET /api/admin/users` for user list. `POST /api/admin/users` to create. `PUT /api/admin/users/{id}/deactivate` to deactivate.
- **To Task 16:** Adapter cards and user table need dark mode styling. Pipeline monitoring charts reuse TimeSeriesChart from Task 14.
- **Decision:** Combining adapters, AI pipeline monitoring, and user management into one task because they share the admin layout and are relatively independent. Schema mapping is a static visualization (mock data) since adapters are mocked anyway. The three tabs (Adapter Health, Schema Mapping, AI Pipeline) keep the page organized.
