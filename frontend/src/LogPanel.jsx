import React from "react";
import { motion } from "motion/react";
import { Sparkles, Library, Settings, Film, User, LogOut, ShieldCheck, Crown } from "lucide-react";
import StorageIndicator from "./StorageIndicator";
import { hasPremiumAccess } from "../api/client";

export default function Navbar({ currentTab, setCurrentTab, currentUser, onLoginClick, onLogout, onUpgradeRequest, storage }) {
  const isAdmin = currentUser?.role === "Super Admin";

  const tabs = [
    { id: "studio", label: "ESTUDIO DE PRODUCCIÓN", icon: Sparkles },
    { id: "library", label: "BIBLIOTECA", icon: Library },
    { id: "settings", label: "AJUSTES & CREDENCIALES", icon: Settings },
    ...(isAdmin ? [{ id: "admin", label: "PANEL ADMIN", icon: ShieldCheck }] : []),
  ];

  return (
    <>
      <header
        className="h-16 bg-[#0E0D0F] border-b border-[#2A262E] px-6 flex items-center justify-between select-none relative z-30 shadow-md"
        style={{ backgroundColor: "#0E0D0F" }}
      >
        {/* Brand Logo on Left */}
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

        {/* Floating Centered Navigation Tabs */}
        <nav
          aria-label="Navegación principal"
          className="flex items-center gap-1 lg:gap-4 xl:gap-8"
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

        {/* Right Section: Storage & User Profile */}
        <div className="flex items-center gap-3">
          {/* Storage quota pill */}
          <StorageIndicator storage={storage} variant="pill" className="hidden xl:flex" />

          {/* User Button */}
          {currentUser ? (
            <div className="flex items-center gap-2 pl-2 border-l border-[#2A262E]">
              {!hasPremiumAccess(currentUser) && (
                <button
                  onClick={onUpgradeRequest}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 rounded-xl text-xs font-mono font-bold transition-colors cursor-pointer"
                >
                  <Crown className="w-3.5 h-3.5" />
                  <span>Mejorar a Pro</span>
                </button>
              )}
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#141217] border border-[#2A262E] rounded-xl text-xs font-mono text-[#ECE7E1]">
                <User className="w-3.5 h-3.5 text-[#E5484D]" />
                <span className="max-w-[120px] truncate">{currentUser.email}</span>
                <span
                  className={`text-[8px] font-bold px-1.5 py-0.5 rounded border uppercase ${
                    isAdmin
                      ? "bg-[#9F1D20]/20 text-[#E5484D] border-[#E5484D]/40"
                      : hasPremiumAccess(currentUser)
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                      : "bg-[#232029] text-[#8E8780] border-[#2A262E]"
                  }`}
                >
                  {isAdmin ? "Admin" : hasPremiumAccess(currentUser) ? "Pro" : "Free"}
                </span>
              </div>
              <button
                onClick={onLogout}
                title="Cerrar sesión"
                className="p-2 text-[#8E8780] hover:text-[#E5484D] hover:bg-[#141217] rounded-xl transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onLoginClick}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[#1E1A24] hover:bg-[#2A2433] border border-[#E5484D]/40 text-[#ECE7E1] rounded-xl text-xs font-mono font-bold transition-all shadow-sm cursor-pointer"
            >
              <User className="w-3.5 h-3.5 text-[#E5484D]" />
              <span>Cuenta</span>
            </button>
          )}
        </div>
      </header>

    </>
  );
}
