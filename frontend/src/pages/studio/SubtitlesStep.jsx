import React, { useState, useEffect } from "react";
import { Subtitles, CheckCircle2 } from "lucide-react";
import Field from "../../components/ui/Field";
import Button from "../../components/ui/Button";

export default function SubtitlesStep({ project, onRunStep, loading }) {
  const [wordsPerCard, setWordsPerCard] = useState(project?.words_per_card || 3);
  const [language, setLanguage] = useState(project?.language || "es");
  const [srtContent, setSrtContent] = useState("");

  const srtPath = project?.subtitles_result?.srt_path;
  const subsDone = Boolean(srtPath);

  useEffect(() => {
    if (srtPath) {
      fetch(`/media/${srtPath}`)
        .then((r) => r.text())
        .then((txt) => setSrtContent(txt))
        .catch(console.error);
    }
  }, [srtPath]);

  const handleGenerate = () => {
    onRunStep("generate_subtitles", {
      words_per_card: parseInt(wordsPerCard),
      language: language || undefined,
    });
  };

  return (
    <div className="space-y-6 max-w-3xl animate-fade-in">
      <div className="border-b border-[#2A262E] pb-4">
        <h2 className="text-lg font-bold font-display text-[#ECE7E1] uppercase tracking-wide">
          5. Generación de Subtítulos (OpenAI Whisper)
        </h2>
        <p className="text-xs text-[#8E8780] mt-1">
          Transcribe el audio mezclado palabra por palabra para generar las tarjetas de subtítulos sincronizados.
        </p>
      </div>

      <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field
            label="Palabras por Tarjeta"
            description="Cantidad de palabras visibles al mismo tiempo en pantalla"
          >
            <select
              value={wordsPerCard}
              onChange={(e) => setWordsPerCard(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm text-[#ECE7E1]"
            >
              <option value="1">1 palabra (Dinámico / TikTok)</option>
              <option value="2">2 palabras</option>
              <option value="3">3 palabras (Estándar)</option>
              <option value="5">5 palabras</option>
            </select>
          </Field>

          <Field label="Idioma de Transcripción">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm text-[#ECE7E1]"
            >
              <option value="es">Español (es)</option>
              <option value="en">Inglés (en)</option>
            </select>
          </Field>
        </div>

        <div className="pt-2 flex justify-end">
          <Button
            variant="primary"
            icon={Subtitles}
            loading={loading}
            onClick={handleGenerate}
          >
            {subsDone ? "Volver a Generar Subtítulos" : "Generar Subtítulos con Whisper"}
          </Button>
        </div>

        {subsDone && (
          <div className="space-y-4 pt-4 border-t border-[#2A262E]">
            <div className="p-3 bg-[#0E0D0F] border border-emerald-800/40 rounded-xl text-xs text-emerald-400 font-mono flex items-center justify-between">
              <span className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Subtítulos SRT Generados con Éxito
              </span>
              <span className="text-[10px] text-[#8E8780] truncate max-w-xs">{srtPath}</span>
            </div>

            {/* Subtitle Cue File Preview */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-[#ECE7E1] uppercase tracking-wider">
                Vista Previa de Cues de Subtítulos (.srt)
              </h4>
              <div className="p-4 bg-[#0E0D0F] border border-[#2A262E] rounded-xl font-mono text-xs text-[#8E8780] max-h-56 overflow-y-auto space-y-2 custom-scrollbar">
                {srtContent ? (
                  <pre className="whitespace-pre-wrap text-[11px] text-[#ECE7E1] leading-relaxed">
                    {srtContent}
                  </pre>
                ) : (
                  <p className="italic text-[11px] text-[#5C554E]">Cargando vista previa del archivo SRT...</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
