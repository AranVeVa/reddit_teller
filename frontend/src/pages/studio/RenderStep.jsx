import React, { useState } from "react";
import { Film, Download, Moon, Sun, Sparkles, CheckCircle2, Activity, XCircle, Lock } from "lucide-react";
import Field from "../../components/ui/Field";
import Button from "../../components/ui/Button";
import ProgressBar from "../../components/ui/ProgressBar";

export default function RenderStep({ project, onRunStep, loading, events = [], onCancelJob, currentUser, onUpgradeRequest }) {
  const [darkMode, setDarkMode] = useState(project?.dark_mode ?? true);
  const [fastMode, setFastMode] = useState(false);
  const [showPaywall, setShowPaywall] = useState(false);

  const isScenes = project?.background_type === "scenes";
  const isPremium = currentUser?.role === "premium" || currentUser?.role === "Super Admin" || currentUser?.isPremium;
  const requiresPremium = isScenes && !isPremium;

  const handleRender = () => {
    if (requiresPremium) {
      setShowPaywall(true);
      return;
    }

    onRunStep("render_video", {
      dark_mode: darkMode,
      fast_mode: fastMode,
      use_scenes: isScenes,
      background_video_path: project?.background_video_path,
      start_second: project?.start_second || 0,
    });
  };

  const videoDone = Boolean(project?.final_video_path);

  const renderLogs = events.filter((e) => e.msg || e.message);
  const latestRenderLog = renderLogs.length > 0 ? renderLogs[renderLogs.length - 1].msg || renderLogs[renderLogs.length - 1].message : null;

  const lastProgressEvt = events.filter((e) => e.type === "progress").pop();
  const percent = lastProgressEvt ? lastProgressEvt.percent : loading ? 50 : videoDone ? 100 : 0;

  return (
    <div className="space-y-6 w-full max-w-5xl mx-auto animate-fade-in relative">
      <div>
        <h2 className="text-2xl font-black font-display text-[#ECE7E1] uppercase tracking-wider flex items-center gap-3">
          7. Renderizado Final del Video MP4
          {requiresPremium && <span className="px-2 py-1 bg-amber-500/10 text-amber-400 text-[10px] rounded border border-amber-500/20 flex items-center gap-1"><Lock className="w-3 h-3" /> PRO</span>}
        </h2>
        <p className="text-xs text-[#8E8780] mt-1">
          Ajusta las opciones finales de la tarjeta de Reddit y compila el video vertical con MoviePy.
        </p>
      </div>

      <div className="p-4 bg-[#141217] border border-[#2A262E] rounded-2xl flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#9F1D20]/20 border border-[#E5484D]/30 flex items-center justify-center text-[#E5484D]">
            <Film className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[#8E8780] font-mono text-[10px] block">MODO DE FONDO CONFIGURADO:</span>
            <span className="font-bold text-[#ECE7E1] uppercase">
              {isScenes ? "Escenas IA (Papercraft 3D)" : `Video Clásico (${project?.background_video_path || "predeterminado"})`}
            </span>
          </div>
        </div>

        {!isScenes && (
          <span className="px-3 py-1 bg-[#0E0D0F] border border-[#2A262E] rounded-lg font-mono text-[11px] text-[#E5484D]">
            Inicio: {project?.start_second || 0}s
          </span>
        )}
      </div>

      <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Tema de Tarjeta Reddit">
            <button
              type="button"
              onClick={() => setDarkMode(!darkMode)}
              className="w-full flex items-center justify-between px-4 py-3 bg-[#0E0D0F] border border-[#2A262E] hover:border-[#E5484D] rounded-xl text-xs font-semibold text-[#ECE7E1] cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-2">
                {darkMode ? <Moon className="w-4 h-4 text-[#E5484D]" /> : <Sun className="w-4 h-4 text-amber-400" />}
                <span>{darkMode ? "Modo Oscuro (Dark Card)" : "Modo Claro (Light Card)"}</span>
              </div>
              <span className="text-[10px] text-[#8E8780]">Cambiar</span>
            </button>
          </Field>

          <Field label="Modo Rápido (Fast Mode)">
            <button
              type="button"
              onClick={() => setFastMode(!fastMode)}
              className={`w-full flex items-center justify-between px-4 py-3 border rounded-xl text-xs font-semibold cursor-pointer transition-colors ${fastMode
                  ? "bg-amber-950/40 border-amber-800/60 text-amber-300"
                  : "bg-[#0E0D0F] border-[#2A262E] text-[#8E8780]"
                }`}
            >
              <span>{fastMode ? "Modo Rápido Activado (12fps)" : "Alta Calidad (60s/30fps)"}</span>
              <span className="text-[10px] uppercase font-mono">{fastMode ? "ON" : "OFF"}</span>
            </button>
          </Field>
        </div>

        {loading && (
          <div className="space-y-3 p-4 bg-[#0E0D0F] border border-[#2A262E] rounded-xl animate-fade-in">
            <ProgressBar percent={percent} label="Compilando fotogramas y mezclas de audio/video..." />

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2 text-[11px] font-mono text-cyan-300 truncate max-w-md">
                <Activity className="w-3.5 h-3.5 animate-spin shrink-0 text-[#E5484D]" />
                <span className="truncate">{latestRenderLog || "Iniciando compilación de video MP4..."}</span>
              </div>

              {onCancelJob && (
                <Button
                  variant="secondary"
                  size="sm"
                  icon={XCircle}
                  onClick={onCancelJob}
                  className="text-red-400 border-red-900/50 hover:bg-red-950/50 shrink-0"
                >
                  Cancelar Render
                </Button>
              )}
            </div>
          </div>
        )}

        <div className="pt-2 flex justify-end">
          <Button
            variant={requiresPremium ? "secondary" : "primary"}
            size="lg"
            icon={requiresPremium ? Lock : Film}
            loading={loading}
            onClick={handleRender}
            className={requiresPremium ? "text-amber-400 border-amber-900/50 hover:bg-amber-950/30" : ""}
          >
            {videoDone ? "Regenerar Render Final" : (requiresPremium ? "Desbloquear Renderizado IA" : "Comenzar Renderizado Final")}
          </Button>
        </div>

        {videoDone && (
          <div className="p-5 bg-[#0E0D0F] border border-[#2A262E] rounded-2xl space-y-4 animate-fade-in mt-6">
            <div className="flex items-center justify-between border-b border-[#2A262E] pb-3">
              <h3 className="text-sm font-bold text-emerald-400 font-mono flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" /> ¡Video Renderizado con Éxito!
              </h3>
              <a
                href={`/media/${project.final_video_path}`}
                download
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#9F1D20] hover:bg-[#B3261E] text-[#ECE7E1] text-xs font-bold rounded-xl shadow-lg shadow-[#9F1D20]/30 transition-all cursor-pointer"
              >
                <Download className="w-4 h-4" /> Descargar MP4
              </a>
            </div>

            <div className="aspect-[9/16] max-h-96 mx-auto bg-black rounded-xl overflow-hidden border border-[#2A262E] shadow-2xl">
              <video
                src={`/media/${project.final_video_path}`}
                controls
                className="w-full h-full object-contain"
              />
            </div>
          </div>
        )}
      </div>

      {showPaywall && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl shadow-amber-900/20 text-center">
            <div className="w-16 h-16 bg-gradient-to-tr from-amber-500 to-yellow-300 rounded-2xl mx-auto flex items-center justify-center mb-6 shadow-lg">
              <Sparkles className="w-8 h-8 text-[#141217]" />
            </div>
            <h3 className="text-xl font-black text-[#ECE7E1] mb-2 uppercase">Renderizado IA Premium</h3>
            <p className="text-sm text-[#8E8780] mb-8">
              El uso de modelos visuales IA para generar escenas dinámicas requiere una suscripción activa.
            </p>

            <div className="flex flex-col gap-3">
              <button
                onClick={() => { setShowPaywall(false); onUpgradeRequest(); }}
                className="w-full py-3 px-4 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white font-bold rounded-xl text-sm transition-all shadow-lg cursor-pointer"
              >
                Actualizar a Pro ($9.99/mes)
              </button>
              <button
                onClick={() => setShowPaywall(false)}
                className="w-full py-3 px-4 bg-transparent border border-[#2A262E] hover:bg-[#2A262E] text-[#8E8780] hover:text-[#ECE7E1] font-semibold rounded-xl text-sm transition-all cursor-pointer"
              >
                Volver al editor
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}