import React, { useState } from "react";
import { Sparkles, Video, Lock, Image as ImageIcon, ChevronRight } from "lucide-react";
import Button from "../../components/ui/Button";
import Field from "../../components/ui/Field";

export default function BackgroundStep({ project, onRunStep, loading, onUpdateProject, currentUser, onUpgradeRequest }) {
  const [showPaywall, setShowPaywall] = useState(false);

  const isPremium = currentUser?.role === "premium" || currentUser?.role === "Super Admin" || currentUser?.isPremium;
  const isScenes = project?.background_type === "scenes";

  const handleSelectType = (type) => {
    onUpdateProject({ background_type: type });
  };

  const handleGeneratePlan = () => {
    if (!isPremium) {
      setShowPaywall(true);
      return;
    }
    onRunStep("generate_scene_plan");
  };

  const handleGenerateImages = () => {
    if (!isPremium) {
      setShowPaywall(true);
      return;
    }
    onRunStep("generate_images");
  };

  return (
    <div className="space-y-6 w-full max-w-5xl mx-auto animate-fade-in relative">
      <div>
        <h2 className="text-2xl font-black font-display text-[#ECE7E1] uppercase tracking-wider flex items-center gap-3">
          6. Configuración del Fondo (Escenas IA vs Clásico)
        </h2>
        <p className="text-xs text-[#8E8780] mt-1">
          Elige entre generar escenas visuales 3D con IA o usar un video en bucle de fondo.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          type="button"
          onClick={() => handleSelectType("scenes")}
          className={`text-left p-5 rounded-2xl border transition-all relative overflow-hidden ${isScenes
              ? "bg-[#141217] border-[#E5484D] shadow-[0_0_15px_rgba(229,72,77,0.1)]"
              : "bg-[#0E0D0F] border-[#2A262E] hover:border-[#8E8780]"
            }`}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className={`w-5 h-5 ${isScenes ? "text-[#E5484D]" : "text-[#8E8780]"}`} />
              <span className={`font-bold text-sm ${isScenes ? "text-[#ECE7E1]" : "text-[#8E8780]"}`}>
                Escenas IA (Recomendado)
              </span>
            </div>
            {!isPremium && (
              <span className="px-2 py-1 bg-amber-500/10 text-amber-400 text-[10px] rounded border border-amber-500/20 flex items-center gap-1">
                <Lock className="w-3 h-3" /> PRO
              </span>
            )}
          </div>
          <p className="text-xs text-[#8E8780] leading-relaxed">
            GPT-4o analiza la historia y genera imágenes de escenas en estilo visual 3D con animación Ken Burns.
          </p>
        </button>

        <button
          type="button"
          onClick={() => handleSelectType("video")}
          className={`text-left p-5 rounded-2xl border transition-all ${!isScenes
              ? "bg-[#141217] border-[#E5484D] shadow-[0_0_15px_rgba(229,72,77,0.1)]"
              : "bg-[#0E0D0F] border-[#2A262E] hover:border-[#8E8780]"
            }`}
        >
          <div className="flex items-center gap-2 mb-3">
            <Video className={`w-5 h-5 ${!isScenes ? "text-[#E5484D]" : "text-[#8E8780]"}`} />
            <span className={`font-bold text-sm ${!isScenes ? "text-[#ECE7E1]" : "text-[#8E8780]"}`}>
              Video Clásico
            </span>
          </div>
          <p className="text-xs text-[#8E8780] leading-relaxed">
            Usa un video de fondo de alta resolución (Minecraft, Subway Surfers, Parkour) recortado dinámicamente.
          </p>
        </button>
      </div>

      {isScenes && (
        <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-5 animate-fade-in">
          <div className="flex items-center gap-3 border-b border-[#2A262E] pb-4">
            <div className="w-8 h-8 rounded-lg bg-[#9F1D20]/20 border border-[#E5484D]/30 flex items-center justify-center text-[#E5484D]">
              <ImageIcon className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#ECE7E1]">Generador de Escenas IA (gpt-4o / DALL-E 3)</h3>
              <p className="text-[10px] text-[#8E8780] uppercase tracking-wider mt-0.5">
                Paso 1: Generar plan de escenas • Paso 2: Renderizar imágenes PNG
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between bg-[#0E0D0F] p-4 rounded-xl border border-[#2A262E]">
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[#2A262E] text-xs font-bold text-[#8E8780]">1</span>
              <span className="text-sm font-medium text-[#ECE7E1]">Estructurar Plan Visual</span>
            </div>
            <Button
              variant={!isPremium ? "secondary" : "primary"}
              size="sm"
              onClick={handleGeneratePlan}
              loading={loading}
              icon={!isPremium ? Lock : ChevronRight}
              className={!isPremium ? "text-amber-400 border-amber-900/50 hover:bg-amber-950/30" : ""}
            >
              1. Generar Plan de Escenas
            </Button>
          </div>

          {project?.scene_plan && (
            <div className="flex items-center justify-between bg-[#0E0D0F] p-4 rounded-xl border border-[#2A262E] animate-fade-in">
              <div className="flex items-center gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[#2A262E] text-xs font-bold text-[#8E8780]">2</span>
                <span className="text-sm font-medium text-[#ECE7E1]">Renderizar en DALL-E 3</span>
              </div>
              <Button
                variant={!isPremium ? "secondary" : "primary"}
                size="sm"
                onClick={handleGenerateImages}
                loading={loading}
                icon={!isPremium ? Lock : Sparkles}
                className={!isPremium ? "text-amber-400 border-amber-900/50 hover:bg-amber-950/30" : ""}
              >
                2. Generar Imágenes
              </Button>
            </div>
          )}
        </div>
      )}

      {showPaywall && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl shadow-amber-900/20 text-center">
            <div className="w-16 h-16 bg-gradient-to-tr from-amber-500 to-yellow-300 rounded-2xl mx-auto flex items-center justify-center mb-6 shadow-lg">
              <Sparkles className="w-8 h-8 text-[#141217]" />
            </div>
            <h3 className="text-xl font-black text-[#ECE7E1] mb-2 uppercase">Generación IA Premium</h3>
            <p className="text-sm text-[#8E8780] mb-8">
              El uso de modelos visuales como GPT-4o y DALL-E 3 consume créditos de API. Para continuar, actualiza tu plan a <strong className="text-amber-400">Pro</strong>.
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
                Volver y usar Video Clásico
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}