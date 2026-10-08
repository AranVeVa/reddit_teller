import React, { useRef, useState, useEffect } from "react";
import { motion } from "motion/react";
import { Sparkles, Library, Settings, Film } from "lucide-react";

export default function Navbar({ currentTab, setCurrentTab }) {
  const tabs = [
    { id: "studio", label: "ESTUDIO DE PRODUCCIÓN", icon: Sparkles },
    { id: "library", label: "BIBLIOTECA", icon: Library },
    { id: "settings", label: "AJUSTES & CREDENCIALES", icon: Settings },
  ];

  return (
    <header
      className="h-16 bg-[#0E0D0F] border-b border-[#2A262E] px-6 flex items-center justify-between select-none relative z-30 shadow-md"
      style={{ backgroundColor: "#0E0D0F" }}
    >
      {/* Smaller Brand Logo on Left */}
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-[#9F1D20] flex items-center justify-center text-white shadow-sm border border-[#E5484D]/40">
          <Film className="w-4 h-4 text-white" />
        </div>
        <div className="flex items-center gap-1.5">
          <span className="font-display text-base font-black tracking-widest text-[#ECE7E1]">
            REDDIT_TELLER
          </span>
          <span className="text-[8px] font-bold font-mono px-1.5 py-0.5 rounded bg-[#232029] text-[#E5484D] border border-[#2A262E] uppercase">
            PRO
          </span>
        </div>
      </div>

      {/* Floating Centered Navigation Tabs - No container border/background, wide spacing */}
      <nav
        aria-label="Navegación principal"
        className="flex items-center gap-6 md:gap-8"
      >
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = currentTab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setCurrentTab(t.id)}
              className="relative flex items-center gap-2 px-4 py-2 text-sm font-bold font-mono tracking-wider cursor-pointer select-none transition-colors duration-200"
              style={{ color: isActive ? "#ECE7E1" : "#8E8780" }}
            >
              {/* Active Pill Indicator */}
              {isActive && (
                <motion.div
                  layoutId="activeNavPill"
                  className="absolute inset-0 bg-[#E5484D] rounded-xl shadow-md z-[-1]"
                  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                />
              )}
              <Icon className="w-4 h-4 shrink-0" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right Spacer for Centering */}
      <div className="w-28 hidden md:block" />
    </header>
  );
}