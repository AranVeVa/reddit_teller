import React, { useState } from "react";
import { Globe, ArrowRight, Search } from "lucide-react";
import Field from "../../components/ui/Field";
import Button from "../../components/ui/Button";

export default function SourceStep({ project, onRunStep, loading }) {
  const [subreddit, setSubreddit] = useState(project?.subreddit || "nosleep");
  const [order, setOrder] = useState(project?.order || "hot");
  const [durationPreset, setDurationPreset] = useState(project?.duration_preset || "1");
  const [limit, setLimit] = useState(project?.limit || 1);

  const handleSearch = () => {
    let minChars = 300;
    let maxChars = 1500;
    if (durationPreset === "1") {
      minChars = 300;
      maxChars = 1400;
    } else if (durationPreset === "2") {
      minChars = 1500;
      maxChars = 3500;
    } else if (durationPreset === "3") {
      minChars = 3500;
      maxChars = 6000;
    }

    onRunStep("search_stories", {
      subreddit: subreddit.replace(/^r\//, "").trim(),
      order,
      duration_preset: durationPreset,
      limit: parseInt(limit),
      min_chars: minChars,
      max_chars: maxChars,
    });
  };

  return (
    <div className="space-y-6 w-full max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-black font-display text-[#ECE7E1] uppercase tracking-wider">
          1. Selección de Fuente & Parámetros
        </h2>
        <p className="text-xs text-[#A39C96] mt-1">
          Indica el subreddit y la duración estimada para buscar historias en Reddit.
        </p>
      </div>

      <div className="bg-[#17151A] border border-[#2E2A31] rounded-xl p-6 space-y-5">
        <Field
          label="Subreddit"
          description="Nombre del subreddit (ej. nosleep, shortscarystories, AskReddit)"
          required
        >
          <div className="relative flex items-center">
            <span className="absolute left-3 text-[#A39C96] font-mono text-sm">r/</span>
            <input
              type="text"
              value={subreddit}
              onChange={(e) => setSubreddit(e.target.value)}
              placeholder="nosleep"
              className="w-full pl-8 pr-3 py-2 bg-[#0E0D0F] border border-[#2E2A31] focus:border-[#E5484D] rounded-lg text-sm text-[#ECE7E1]"
            />
          </div>
        </Field>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Orden de Publicaciones">
            <select
              value={order}
              onChange={(e) => setOrder(e.target.value)}
              className="w-full px-3 py-2 bg-[#0E0D0F] border border-[#2E2A31] focus:border-[#E5484D] rounded-lg text-sm text-[#ECE7E1]"
            >
              <option value="hot">Tendencia (Hot)</option>
              <option value="new">Recientes (New)</option>
              <option value="top">Más Relevantes (Top)</option>
            </select>
          </Field>

          <Field label="Número de Historias">
            <input
              type="number"
              min="1"
              max="5"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              className="w-full px-3 py-2 bg-[#0E0D0F] border border-[#2E2A31] focus:border-[#E5484D] rounded-lg text-sm font-mono text-[#ECE7E1]"
            />
          </Field>
        </div>

        <Field label="Preset de Duración Estimada">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: "1", title: "Shorts (~60s)", sub: "300-1400 caract." },
              { id: "2", title: "Corto (~3min)", sub: "1500-3500 caract." },
              { id: "3", title: "Medio (~5min)", sub: "3500-6000 caract." },
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setDurationPreset(p.id)}
                className={`p-3 rounded-lg border text-left transition-all cursor-pointer ${
                  durationPreset === p.id
                    ? "bg-[#2B272F] border-[#E5484D] text-[#ECE7E1]"
                    : "bg-[#0E0D0F] border-[#2E2A31] text-[#A39C96] hover:border-[#45404A]"
                }`}
              >
                <p className="text-xs font-bold text-[#ECE7E1]">{p.title}</p>
                <p className="text-[10px] text-[#A39C96] mt-0.5">{p.sub}</p>
              </button>
            ))}
          </div>
        </Field>

        <div className="pt-2 flex justify-end">
          <Button
            variant="primary"
            icon={Search}
            loading={loading}
            onClick={handleSearch}
          >
            Buscar Candidatos en Reddit
          </Button>
        </div>
      </div>
    </div>
  );
}
