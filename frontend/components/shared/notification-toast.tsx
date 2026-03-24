"use client";

import { toast } from "sonner";
import { CheckCircle2, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { createElement } from "react";

type ToastVariant = "success" | "error" | "info" | "warning";

interface NotifyOptions {
  title: string;
  description?: string;
  variant?: ToastVariant;
}

const VARIANT_ICONS = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

export function notify({ title, description, variant = "info" }: NotifyOptions) {
  const Icon = VARIANT_ICONS[variant];
  const icon = createElement(Icon, { className: "h-4 w-4" });

  switch (variant) {
    case "success":
      toast.success(title, { description, icon });
      break;
    case "error":
      toast.error(title, { description, icon });
      break;
    case "warning":
      toast.warning(title, { description, icon });
      break;
    default:
      toast.info(title, { description, icon });
      break;
  }
}

export function useNotify() {
  return notify;
}
