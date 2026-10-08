import React from "react";

export default function CheckAnimation({ message = "¡Guardado con éxito!", className = "" }) {
  return (
    <div className={`flex items-center gap-3 p-3.5 bg-[#0E0D0F] border border-emerald-500/40 rounded-2xl shadow-lg shadow-emerald-950/20 animate-fade-in ${className}`}>
      {/* Animated SVG Check Circle (Apple Pay style) */}
      <div className="relative w-7 h-7 flex items-center justify-center shrink-0">
        <svg className="w-7 h-7" viewBox="0 0 52 52">
          <circle
            className="text-emerald-500 stroke-current animate-draw-circle"
            cx="26"
            cy="26"
            r="23"
            fill="none"
            strokeWidth="4"
          />
          <path
            className="text-emerald-400 stroke-current animate-draw-check"
            fill="none"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M14.1 27.2l7.1 7.2 16.7-16.8"
          />
        </svg>
      </div>

      <span className="text-xs font-mono font-bold text-emerald-300 tracking-wide">
        {message}
      </span>
    </div>
  );
}
