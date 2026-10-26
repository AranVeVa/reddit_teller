import React from "react";

export default function Field({
  label,
  description,
  error,
  required = false,
  children,
  className = "",
}) {
  return (
    <div className={`space-y-1.5 ${className}`}>
      {label && (
        <label className="block text-xs font-semibold text-[#ECE7E1] uppercase tracking-wider">
          {label}
          {required && <span className="text-[#E5484D] ml-1">*</span>}
        </label>
      )}

      {children}

      {description && (
        <p className="text-xs text-[#A39C96] leading-relaxed">{description}</p>
      )}

      {error && (
        <p className="text-xs text-red-400 font-medium flex items-center gap-1">
          <span>⚠</span> {error}
        </p>
      )}
    </div>
  );
}
