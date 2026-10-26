import React from "react";
import { HardDrive, Trash2, Loader2 } from "lucide-react";

/**
 * Indicador "54.2 MB / 350 MB" con botón de limpieza.
 * variant="pill" (Navbar) | "bar" (pie del estudio, con barra de progreso).
 */
export default function StorageIndicator({ storage, variant = "pill", className = "" }) {
  const { stats, cleaning, message, cleanup } = storage || {};
  if (!stats) return null;

  const near = stats.is_near_limit;
  const handleClean = () => {
    if (cleaning) return;
    if (window.confirm("Se borrarán los audios generados y los renders antiguos (se conserva el último MP4). ¿Continuar?")) {
      cleanup();
    }
  };

  const button = (
    <button
      type="button"
      onClick={handleClean}
      disabled={cleaning}
      title="Limpiar almacenamiento: borra audios generados y renders antiguos"
      className="p-1 hover:text-[#E5484D] rounded transition-colors cursor-pointer disabled:opacity-50"
    >
      {cleaning ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
    </button>
  );

  if (variant === "bar") {
    return (
      <div className={`p-4 bg-[#141217] border border-[#2A262E] rounded-2xl space-y-2 ${className}`}>
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="flex items-center gap-2 text-[#8E8780]">
            <HardDrive className={`w-4 h-4 ${near ? "text-amber-400" : "text-[#E5484D]"}`} />
            Almacenamiento
          </span>
          <span className="flex items-center gap-2 text-[#ECE7E1] font-bold">
            {stats.used_mb} MB / {stats.max_mb} MB
            <span className="text-[#8E8780] font-normal">
              <button
                type="button"
                onClick={handleClean}
                disabled={cleaning}
                className="inline-flex items-center gap-1 px-2 py-1 border border-[#2A262E] hover:border-[#E5484D] rounded-lg text-[10px] text-[#8E8780] hover:text-[#ECE7E1] transition-colors cursor-pointer disabled:opacity-50"
              >
                {cleaning ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                Borrar almacenamiento
              </button>
            </span>
          </span>
        </div>
        <div className="h-1.5 bg-[#0E0D0F] rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${near ? "bg-amber-400" : "bg-[#E5484D]"}`}
            style={{ width: `${Math.min(100, stats.percent)}%` }}
          />
        </div>
        {(near || message) && (
          <p className="text-[10px] font-mono text-amber-300">
            {message || "Cerca del límite gratuito: libera espacio antes de renderizar."}
          </p>
        )}
      </div>
    );
  }

  return (
    <div
      title={message || `Almacenamiento: ${stats.used_mb} MB / ${stats.max_mb} MB (${stats.percent}%)`}
      className={`flex items-center gap-2 px-3 py-1.5 bg-[#141217] border border-[#2A262E] rounded-xl text-xs font-mono text-[#8E8780] ${className}`}
    >
      <HardDrive className={`w-3.5 h-3.5 ${near ? "text-amber-400 animate-pulse" : "text-[#E5484D]"}`} />
      <span className="text-[#ECE7E1] font-bold">{message || `${stats.used_mb} MB`}</span>
      {!message && <span className="text-[10px] text-[#6E6760]">/ {stats.max_mb} MB</span>}
      {button}
    </div>
  );
}
