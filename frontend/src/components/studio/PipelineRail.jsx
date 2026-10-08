import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Globe,
  FileText,
  Edit3,
  Mic,
  Subtitles,
  Image as ImageIcon,
  Film,
  CheckCircle2,
  Clock,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export const PIPELINE_STEPS = [
  { id: 1, key: "source", title: "Fuente", desc: "Subreddit & Filtros", icon: Globe },
  { id: 2, key: "stories", title: "Historias", desc: "Selección & Score", icon: FileText },
  { id: 3, key: "edit", title: "Edición", desc: "Pulido de Texto", icon: Edit3 },
  { id: 4, key: "voice", title: "Voz & Mezcla", desc: "ElevenLabs & Audio", icon: Mic },
  { id: 5, key: "subtitles", title: "Subtítulos", desc: "Whisper SRT", icon: Subtitles },
  { id: 6, key: "background", title: "Fondo", desc: "Escenas IA vs Clásico", icon: ImageIcon },
  { id: 7, key: "render", title: "Render", desc: "MoviePy Final MP4", icon: Film },
];

const springConfig = { type: "spring", stiffness: 850, damping: 45, mass: 0.3 };

export default function PipelineRail({ currentStep, setCurrentStep, project, loading }) {
  const [collapsed, setCollapsed] = useState(false);

  const getStepStatus = (stepId) => {
    if (!project) return "pending";
    if (stepId < project.current_step) return "completed";
    if (stepId === project.current_step) return "active";
    return "pending";
  };

  const handleStepClick = (stepId) => {
    if (loading) {
      if (!window.confirm("Hay un proceso del pipeline en curso. ¿Deseas cambiar de paso de todos modos?")) {
        return;
      }
    }
    setCurrentStep(stepId);
  };

  return (
    <motion.nav
      aria-label="Pasos del Pipeline"
      animate={{ width: collapsed ? 68 : 256 }}
      transition={springConfig}
      className="bg-[#141217] border-r border-[#2A262E] shrink-0 select-none flex flex-col justify-between relative overflow-hidden"
      style={{ backgroundColor: "#141217" }} /* Prevents white flash during transition */
    >
      {/* Inner wrapper with fixed width to prevent text jitter during collapse */}
      <div className="w-[256px] flex flex-col h-full">
        <div className="p-3 space-y-1.5 relative">
          {/* Rail Header — fixed height so nothing shifts vertically */}
          <div className="h-10 flex items-center border-b border-[#2A262E]/60 mb-2 px-2 gap-3">
            {/* Toggle button — same left alignment as step icons */}
            <button
              type="button"
              onClick={() => setCollapsed(!collapsed)}
              className="w-9 h-9 flex items-center justify-center shrink-0 text-[#8E8780] hover:text-[#ECE7E1] hover:bg-[#232029] rounded-lg transition-colors cursor-pointer"
              title={collapsed ? "Expandir barra lateral" : "Contraer barra lateral"}
            >
              {collapsed ? <ChevronRight className="w-[18px] h-[18px]" /> : <ChevronLeft className="w-[18px] h-[18px]" />}
            </button>

            <AnimatePresence mode="wait">
              {!collapsed && (
                <motion.div
                  key="header-text"
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  transition={{ duration: 0.12, ease: "easeInOut" }}
                  className="flex items-center gap-2 whitespace-nowrap"
                >
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#8E8780]">
                    ETAPAS DEL PIPELINE
                  </span>
                  <span className="font-mono text-[#E5484D] font-black text-[10px]">
                    {currentStep}/7
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Pipeline Step Buttons with Motion layoutId indicator */}
          {PIPELINE_STEPS.map((s) => {
            const status = getStepStatus(s.id);
            const isActive = currentStep === s.id;
            const Icon = s.icon;

            return (
              <button
                key={s.id}
                type="button"
                onClick={() => handleStepClick(s.id)}
                aria-current={isActive ? "step" : undefined}
                title={collapsed ? `${s.id}. ${s.title}: ${s.desc}` : undefined}
                className="w-full relative flex items-center p-2.5 rounded-2xl text-xs font-semibold text-left cursor-pointer group"
              >
                {/* Sliding Active Background — layoutId ensures smooth animation between steps */}
                {isActive && (
                  <motion.div
                    layoutId="activePipelineStep"
                    className="absolute inset-0 bg-[#232029] border border-[#E5484D]/40 rounded-2xl shadow-md z-0"
                    transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
                  />
                )}

                <div className="flex items-center gap-3 truncate w-full relative z-10">
                  {/* Free Icon */}
                  <div
                    className={`w-9 h-9 flex items-center justify-center shrink-0 transition-colors duration-200 ${
                      isActive
                        ? "text-[#E5484D]"
                        : status === "completed"
                        ? "text-emerald-400"
                        : "text-[#8E8780]"
                    }`}
                  >
                    {status === "completed" ? (
                      <CheckCircle2 className="w-[18px] h-[18px]" />
                    ) : (
                      <Icon className="w-[18px] h-[18px]" />
                    )}
                  </div>

                  {/* Label text — always rendered but hidden via opacity when collapsed */}
                  <AnimatePresence mode="wait">
                    {!collapsed && (
                      <motion.div
                        key="step-label"
                        initial={{ opacity: 0, width: 0, x: -6 }}
                        animate={{ opacity: 1, width: "auto", x: 0 }}
                        exit={{ opacity: 0, width: 0, x: -6 }}
                        transition={{ duration: 0.1, ease: "easeInOut" }}
                        className="flex flex-col truncate overflow-hidden whitespace-nowrap"
                      >
                        <span className={`truncate text-xs font-bold leading-tight ${
                          isActive ? "text-[#ECE7E1]"
                          : status === "completed" ? "text-[#ECE7E1]"
                          : "text-[#8E8780]"
                        }`}>
                          {s.id}. {s.title}
                        </span>
                        <span className={`text-[10px] font-mono leading-none mt-0.5 truncate ${
                          isActive ? "text-[#E5484D] font-semibold" : "text-[#8E8780]"
                        }`}>
                          {s.desc}
                        </span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Status indicator on right */}
                <AnimatePresence mode="wait">
                  {!collapsed && (
                    <motion.div
                      key="status-icon"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.1 }}
                      className="flex items-center gap-1.5 shrink-0 pl-1 relative z-10"
                    >
                      {status === "completed" ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : status === "active" ? (
                        <span className="relative flex h-3 w-3 items-center justify-center">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                        </span>
                      ) : (
                        <Clock className="w-3.5 h-3.5 text-[#5C554E] shrink-0" />
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>
            );
          })}
        </div>

        {/* Collapsible Footer Info */}
        <div className="mt-auto p-3">
          <AnimatePresence mode="wait">
            {!collapsed && (
              <motion.div
                key="footer-info"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.15, ease: "easeInOut" }}
                className="p-3 bg-[#0E0D0F] rounded-xl border border-[#2A262E] text-[10px] font-mono text-[#8E8780] space-y-1 w-full"
              >
                <div className="flex justify-between">
                  <span>Proyecto ID:</span>
                  <span className="text-[#ECE7E1] font-bold">{project?.id || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Modo Fondo:</span>
                  <span className="text-[#E5484D] font-bold uppercase">{project?.background_type || "scenes"}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.nav>
  );
}
