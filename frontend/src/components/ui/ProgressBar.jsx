import React from "react";

export default function ProgressBar({ percent = 0, label, className = "" }) {
  const clampedPercent = Math.min(100, Math.max(0, percent));

  return (
    <div className={`space-y-1.5 ${className}`}>
      {label && (
        <div className="flex justify-between text-xs text-[#A39C96]">
          <span>{label}</span>
          <span className="font-mono text-[#ECE7E1]">{clampedPercent}%</span>
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={clampedPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        className="w-full h-2 bg-[#17151A] border border-[#2E2A31] rounded-full overflow-hidden"
      >
        <div
          className="h-full bg-gradient-to-r from-[#9F1D20] to-[#E5484D] transition-all duration-300 ease-out"
          style={{ width: `${clampedPercent}%` }}
        />
      </div>
    </div>
  );
}
