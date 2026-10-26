import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, Clock, Loader2 } from "lucide-react";

export default function StatusBadge({ status, label }) {
  // status: 'ok' | 'success' | 'warning' | 'error' | 'running' | 'pending'
  const styles = {
    ok: {
      bg: "bg-emerald-950/60 border-emerald-800/60 text-emerald-300",
      icon: CheckCircle2,
      defaultLabel: "Configurado",
    },
    success: {
      bg: "bg-emerald-950/60 border-emerald-800/60 text-emerald-300",
      icon: CheckCircle2,
      defaultLabel: "Completado",
    },
    warning: {
      bg: "bg-amber-950/60 border-amber-800/60 text-amber-300",
      icon: AlertTriangle,
      defaultLabel: "Pendiente",
    },
    error: {
      bg: "bg-red-950/60 border-red-800/60 text-red-300",
      icon: XCircle,
      defaultLabel: "Error",
    },
    running: {
      bg: "bg-blue-950/60 border-blue-800/60 text-blue-300",
      icon: Loader2,
      iconClass: "animate-spin",
      defaultLabel: "Procesando",
    },
    pending: {
      bg: "bg-[#211E24] border-[#2E2A31] text-[#A39C96]",
      icon: Clock,
      defaultLabel: "Sin iniciar",
    },
  };

  const cfg = styles[status] || styles.pending;
  const Icon = cfg.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full border ${cfg.bg}`}
    >
      <Icon className={`w-3.5 h-3.5 ${cfg.iconClass || ""}`} />
      <span>{label || cfg.defaultLabel}</span>
    </span>
  );
}
