import React, { useState } from "react";
import { Check, X, ArrowRight, Eye, Star } from "lucide-react";
import Button from "../../components/ui/Button";

export default function StoriesStep({ project, onRunStep, loading }) {
  const candidates = project?.candidates || [];
  const [accepted, setAccepted] = useState(project?.accepted_stories || []);
  const [expandedId, setExpandedId] = useState(candidates[0]?.id || null);

  const isAccepted = (id) => accepted.some((a) => a.id === id);

  const toggleAccept = (story) => {
    if (isAccepted(story.id)) {
      setAccepted(accepted.filter((a) => a.id !== story.id));
    } else {
      if (accepted.length >= (project?.limit || 1)) {
        // Reemplazar si excede el limite
        setAccepted([story]);
      } else {
        setAccepted([...accepted, story]);
      }
    }
  };

  const handleContinue = () => {
    if (accepted.length === 0) {
      alert("Selecciona al menos una historia para continuar");
      return;
    }

    onRunStep("accept_stories", { accepted_stories: accepted });
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold font-display text-[#ECE7E1] uppercase tracking-wide">
            2. Selección de Historias Candidatas
          </h2>
          <p className="text-xs text-[#A39C96] mt-1">
            Revisa los posts obtenidos de r/{project?.subreddit}. Acepta la historia que deseas procesar.
          </p>
        </div>

        <Button
          variant="primary"
          icon={ArrowRight}
          disabled={accepted.length === 0}
          loading={loading}
          onClick={handleContinue}
        >
          Continuar con {accepted.length} seleccionada(s)
        </Button>
      </div>

      {candidates.length === 0 ? (
        <div className="bg-[#17151A] border border-[#2E2A31] rounded-xl p-8 text-center text-[#A39C96] text-xs">
          No hay historias candidatas cargadas. Regresa al paso 1 para realizar una búsqueda.
        </div>
      ) : (
        <div className="space-y-4">
          {candidates.map((c, idx) => {
            const selected = isAccepted(c.id);
            const isExpanded = expandedId === c.id;

            return (
              <div
                key={c.id}
                className={`bg-[#17151A] border rounded-xl overflow-hidden transition-all ${
                  selected
                    ? "border-[#E5484D] shadow-md shadow-[#9F1D20]/10"
                    : "border-[#2E2A31] hover:border-[#45404A]"
                }`}
              >
                <div className="p-4 flex items-start justify-between gap-4">
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono bg-[#211E24] px-2 py-0.5 rounded text-[#A39C96]">
                        #{idx + 1} • ID: {c.id}
                      </span>
                      <span className="text-[10px] font-semibold text-amber-400 flex items-center gap-1">
                        <Star className="w-3 h-3 fill-current" /> {c.score}
                      </span>
                      <span className="text-[10px] text-[#A39C96]">
                        {c.content?.length || 0} caract. (~{Math.round((c.content?.length || 0) / 14)}s)
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-[#ECE7E1] leading-snug">
                      {c.title}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant={selected ? "primary" : "secondary"}
                      size="sm"
                      icon={selected ? Check : undefined}
                      onClick={() => toggleAccept(c)}
                    >
                      {selected ? "Aceptada" : "Seleccionar"}
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      icon={Eye}
                      onClick={() => setExpandedId(isExpanded ? null : c.id)}
                    >
                      {isExpanded ? "Ocultar" : "Leer"}
                    </Button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="p-4 bg-[#0E0D0F] border-t border-[#2E2A31] text-xs text-[#ECE7E1] font-mono whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto">
                    {c.content}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
