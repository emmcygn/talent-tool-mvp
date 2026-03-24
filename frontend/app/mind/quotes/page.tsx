"use client";

import { useState, useEffect } from "react";
import type { Quote } from "@/contracts/canonical";
import { apiClient } from "@/lib/api-client";
import { QuoteCard } from "@/components/mind/quote-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, Clock, CheckCircle2 } from "lucide-react";

export default function QuotesPage() {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.quotes.list();
        setQuotes(data);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const active = quotes.filter((q) => q.status === "generated" || q.status === "sent");
  const accepted = quotes.filter((q) => q.status === "accepted");
  const declined = quotes.filter((q) => q.status === "declined" || q.status === "expired");

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Quotes</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Review and manage your introduction requests.
        </p>
      </div>

      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active" className="gap-1.5">
            <Clock className="h-4 w-4" />
            Active
            {active.length > 0 && (
              <span className="ml-1 rounded-full bg-blue-100 text-blue-700 px-2 py-0.5 text-xs font-medium">
                {active.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="accepted" className="gap-1.5">
            <CheckCircle2 className="h-4 w-4" />
            Accepted
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-1.5">
            <FileText className="h-4 w-4" />
            History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-4 space-y-4">
          {loading ? (
            Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-64 rounded-lg" />
            ))
          ) : active.length === 0 ? (
            <div className="text-center py-12 border rounded-lg border-dashed">
              <FileText className="h-10 w-10 mx-auto text-muted-foreground/50 mb-3" />
              <p className="text-muted-foreground">No active quotes.</p>
              <p className="text-sm text-muted-foreground mt-1">
                Request an introduction from the candidates page to get started.
              </p>
            </div>
          ) : (
            active.map((q) => (
              <QuoteCard
                key={q.id}
                quote={q}
                onAccept={() => {/* Accept via API */}}
                onDecline={() => {/* Decline via API */}}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="accepted" className="mt-4 space-y-4">
          {accepted.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No accepted quotes yet.
            </p>
          ) : (
            accepted.map((q) => (
              <QuoteCard key={q.id} quote={q} />
            ))
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-4 space-y-3">
          {declined.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No past quotes.
            </p>
          ) : (
            declined.map((q) => (
              <QuoteCard key={q.id} quote={q} compact />
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
