import React, { useRef, useState, useEffect } from "react";
import { motion } from "motion/react";
import { Sparkles, Library, Settings, Film } from "lucide-react";

export default function Navbar({ currentTab, setCurrentTab }) {
  const tabs = [
    { id: "studio", label: "ESTUDIO DE PRODUCCIÓN", icon: Sparkles },
    { id: "library", label: "BIBLIOTECA MP4", icon: Library },
    { id: "settings", label: "AJUSTES & CREDENCIALES", icon: Settings },
  ];

  return (
    <header
      className="h-16 bg-[#0E0D0F] border-b border-[#2A262E] px-8 flex items-center justify-between select-none relative z-30 shadow-md"
      style={{ backgroundColor: "#0E0D0F" }}
    >
      {/* Clean Brand Logo on Left */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[#9F1D20] flex items-center justify-center text-white shadow-md border border-[#E5484D]/40">
          <Film className="w-4 h-4 text-white" />
        </div>
        <div className="flex items-center gap-2">
          <span className="font-display text-lg font-black tracking-widest text-[#ECE7E1]">
            REDDIT_TELLER
          </span>
          <span className="text-[9px] font-bold font-mono px-2 py-0.5 rounded bg-[#232029] text-[#E5484D] border border-[#2A262E] uppercase">
            PRO
          </span>
        </div>
      </div>

      {/* Centered Navigation Tabs with Motion layoutId Sliding Pill */}
      <nav
        aria-label="Navegación principal"
        className="relative flex items-center gap-1 h-10 bg-[#141217] p-1 rounded-xl border border-[#2A262E]"
      >
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = currentTab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setCurrentTab(t.id)}
              className="relative flex items-center gap-2 px-4 py-2 text-xs font-bold font-mono tracking-wider cursor-pointer select-none z-10 rounded-lg transition-colors duration-200"
              style={{ color: isActive ? "#ECE7E1" : "#8E8780" }}
            >
              {/* Sliding Pill Background — layoutId handles smooth animation */}
              {isActive && (
                <motion.div
                  layoutId="activeNavPill"
                  className="absolute inset-0 bg-[#E5484D] rounded-lg shadow-[0_0_16px_rgba(229,72,77,0.35)] z-[-1]"
                  transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
                />
              )}
              <Icon className="w-4 h-4" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right Spacer for Centering */}
      <div className="w-36 hidden md:block" />
    </header>
  );
}