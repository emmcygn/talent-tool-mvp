import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency = "GBP"): string {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency }).format(amount);
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric"
  });
}

export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
}

export function confidenceColor(confidence: string): string {
  switch (confidence) {
    case "strong": return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    case "good": return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    case "possible": return "text-slate-400 bg-slate-500/10 border-slate-500/20";
    default: return "text-slate-500 bg-slate-500/10 border-slate-500/20";
  }
}

export function skillMatchColor(status: string): string {
  switch (status) {
    case "matched": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    case "partial": return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    case "missing": return "bg-slate-500/10 text-slate-500 border-slate-500/20";
    default: return "bg-slate-500/10 text-slate-500 border-slate-500/20";
  }
}
