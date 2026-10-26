import React, { useState, useRef, useEffect } from "react";
import { Terminal, ChevronDown, ChevronUp } from "lucide-react";

export default function LogPanel({ events = [], className = "" }) {
  const [collapsed, setCollapsed] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!collapsed) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [events, collapsed]);

  if (!events || events.length === 0) return null;

  return (
    <div className={`bg-[#17151A] border border-[#2E2A31] rounded-xl overflow-hidden font-mono text-xs ${className}`}>
      <div
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between px-3 py-2 bg-[#211E24] cursor-pointer border-b border-[#2E2A31] select-none"
      >
        <div className="flex items-center gap-2 text-[#A39C96]">
          <Terminal className="w-3.5 h-3.5 text-[#E5484D]" />
          <span className="font-semibold text-[#ECE7E1]">Log de Ejecución</span>
          <span className="text-[10px] bg-[#2B272F] px-1.5 py-0.5 rounded text-[#A39C96]">
            {events.length} entradas
          </span>
        </div>
        <button className="text-[#A39C96] hover:text-[#ECE7E1]">
          {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {!collapsed && (
        <div className="p-3 max-h-48 overflow-y-auto space-y-1 bg-[#0E0D0F]">
          {events.map((evt, idx) => {
            const levelColors = {
              success: "text-emerald-400",
              error: "text-red-400",
              warn: "text-amber-400",
              info: "text-[#7FA7C9]",
            };
            return (
              <div key={idx} className="flex gap-2 leading-relaxed">
                <span className="text-[#6E6760] select-none">&gt;</span>
                <span className={levelColors[evt.level] || "text-[#ECE7E1]"}>
                  {evt.msg}
                </span>
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
