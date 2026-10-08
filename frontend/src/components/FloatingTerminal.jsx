import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Terminal, Maximize2, Minimize2, Activity } from "lucide-react";

export default function FloatingTerminal({ events = [], isRunning = false }) {
  const [mode, setMode] = useState("compact"); // "compact", "open", "expanded"
  const [allLogs, setAllLogs] = useState([]);
  const logsEndRef = useRef(null);

  // Append new events to session logs without wiping previous history
  useEffect(() => {
    if (events && events.length > 0) {
      setAllLogs((prev) => {
        const newEvts = events.filter(
          (e) => !prev.some((p) => p === e || (p.msg && p.msg === e.msg && p.time === e.time))
        );
        return [...prev, ...newEvts];
      });
    }
  }, [events]);

  useEffect(() => {
    if (mode !== "compact") {
      logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [allLogs, mode]);

  // Filter out raw frame progress stdout lines from flooding terminal
  const displayLogs = allLogs.filter((evt) => {
    if (evt.type === "progress") return false;
    const msg = evt.msg || evt.message || "";
    if (typeof msg === "string" && msg.includes("frame=")) return false;
    return true;
  });

  const renderLogMessage = (evt, index) => {
    let msg = evt.msg || evt.message || (typeof evt === "string" ? evt : JSON.stringify(evt));
    let colorClass = "text-[#ECE7E1]";

    if (evt.level === "error" || evt.type === "error") {
      colorClass = "text-red-400 font-bold";
    } else if (evt.level === "warn" || evt.type === "warn") {
      colorClass = "text-amber-400";
    } else if (evt.level === "success" || evt.type === "done") {
      colorClass = "text-emerald-400 font-semibold";
    } else if (evt.level === "info") {
      colorClass = "text-cyan-300";
    }

    return (
      <div
        key={index}
        className="py-0.5 leading-tight flex items-start gap-2 text-[10px] font-mono border-b border-[#1A181F]/40 truncate max-w-full whitespace-nowrap overflow-hidden text-ellipsis select-text"
      >
        <span className="text-[#5C554E] select-none text-[9px] shrink-0">
          {new Date().toLocaleTimeString()}
        </span>
        <span className={`${colorClass} truncate shrink`}>{msg}</span>
      </div>
    );
  };

  const isExpanded = mode === "expanded";

  return (
    <>
      {/* Compact Pill (always present as exit target for AnimatePresence) */}
      <AnimatePresence mode="wait">
        {mode === "compact" && (
          <motion.div
            key="compact-pill"
            initial={{ opacity: 0, y: 16, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.92 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="fixed bottom-5 right-6 z-50"
          >
            <button
              type="button"
              onClick={() => setMode("open")}
              className="flex items-center gap-2 px-4 py-2 bg-[#141217] border border-[#2A262E] hover:border-[#E5484D] rounded-full shadow-2xl text-xs font-mono text-[#ECE7E1] cursor-pointer transition-colors duration-200 hover:scale-105 active:scale-95 group focus:outline-none"
              style={{ backgroundColor: "#141217" }}
            >
              <Terminal className="w-4 h-4 text-[#E5484D] group-hover:rotate-12 transition-transform duration-300" />
              <span className="font-bold tracking-widest text-xs">LOGS</span>
              {isRunning && (
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping ml-1" />
              )}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Open/Expanded Terminal Window */}
      <AnimatePresence mode="wait">
        {mode !== "compact" && (
          <motion.div
            key="terminal-window"
            initial={{ opacity: 0, y: 20, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.94 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className={`fixed z-50 shadow-2xl border rounded-2xl overflow-hidden flex flex-col border-[#2A262E] ${
              isExpanded
                ? "bottom-6 right-6 left-6 top-20 md:left-32 md:right-8 md:bottom-8"
                : "bottom-5 right-6 w-[540px] max-w-[calc(100vw-3rem)] h-64"
            }`}
            style={{ backgroundColor: "#080709" }}
          >
            {/* Header Bar */}
            <div
              className="h-9 border-b border-[#2A262E] px-4 flex items-center justify-between select-none shrink-0"
              style={{ backgroundColor: "#141217" }}
            >
              <div className="flex items-center gap-2.5">
                <Terminal className="w-4 h-4 text-[#E5484D]" />
                <span className="text-xs font-bold font-mono tracking-wider text-[#ECE7E1]">
                  LOG DE EJECUCIÓN
                </span>

                {isRunning ? (
                  <span className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/70 text-emerald-400 border border-emerald-800/40 animate-pulse">
                    <Activity className="w-3 h-3 animate-spin" /> PROCESANDO...
                  </span>
                ) : (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1A181F] text-[#8E8780]">
                    IDLE
                  </span>
                )}
              </div>

              {/* Control Buttons */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setMode("compact")}
                  className="p-1 text-[#8E8780] hover:text-[#ECE7E1] hover:bg-[#232029] rounded-lg transition-colors cursor-pointer focus:outline-none"
                  title="Minimizar a píldora LOGS"
                >
                  <Minimize2 className="w-3.5 h-3.5" />
                </button>

                <button
                  type="button"
                  onClick={() => setMode(isExpanded ? "open" : "expanded")}
                  className="p-1 text-[#8E8780] hover:text-[#ECE7E1] hover:bg-[#232029] rounded-lg transition-colors cursor-pointer focus:outline-none"
                  title={isExpanded ? "Restaurar a tamaño normal" : "Expandir pantalla completa"}
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Terminal Output Stream */}
            <div
              className="flex-1 p-3 overflow-y-auto font-mono text-[10px] space-y-0.5"
              style={{ backgroundColor: "#080709" }}
            >
              {displayLogs.length === 0 ? (
                <div className="h-full flex items-center justify-center text-[#5C554E] italic text-[11px]">
                  No hay comandos ejecutados aún en esta sesión...
                </div>
              ) : (
                displayLogs.map(renderLogMessage)
              )}
              <div ref={logsEndRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
