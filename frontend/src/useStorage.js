import React from "react";
import { Loader2 } from "lucide-react";

export default function Button({
  children,
  variant = "primary", // primary | secondary | danger | ghost
  size = "md", // sm | md | lg
  loading = false,
  disabled = false,
  icon: Icon,
  className = "",
  type = "button",
  onClick,
  ...props
}) {
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none";

  const variants = {
    primary:
      "bg-[#9F1D20] hover:bg-[#B3261E] text-[#ECE7E1] active:scale-[0.98] shadow-sm border border-[#E5484D]/30",
    secondary:
      "bg-[#211E24] hover:bg-[#2B272F] text-[#ECE7E1] border border-[#2E2A31] hover:border-[#45404A]",
    danger:
      "bg-red-900/40 hover:bg-red-900/60 text-red-200 border border-red-700/50",
    ghost:
      "bg-transparent hover:bg-[#211E24] text-[#A39C96] hover:text-[#ECE7E1]",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-sm gap-2",
    lg: "px-5 py-3 text-base gap-2.5 font-semibold",
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`${baseStyles} ${variants[variant] || variants.primary} ${
        sizes[size] || sizes.md
      } ${className}`}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : Icon ? (
        <Icon className="w-4 h-4 shrink-0" />
      ) : null}
      {children}
    </button>
  );
}
