import React, { useState } from "react";
import { Edit3, Save, Clock, Type } from "lucide-react";
import Field from "../../components/ui/Field";
import Button from "../../components/ui/Button";
import CheckAnimation from "../../components/ui/CheckAnimation";

export default function EditStep({ project, onRunStep, loading, onUpdateProject }) {
  const story = project?.accepted_stories?.[0];
  const [title, setTitle] = useState(story?.title || "");
  const [content, setContent] = useState(story?.content || "");
  const [savedSuccess, setSavedSuccess] = useState(false);

  const charCount = content.length;
  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;
  const estimatedSecs = Math.round(charCount / 14);

  const handleSaveText = () => {
    if (!title.trim() || !content.trim()) {
      alert("El título y el contenido no pueden estar vacíos");
      return;
    }

    const updatedStories = [
      {
        id: story?.id || "story_1",
        title: title.trim(),
        content: content.trim(),
        score: story?.score || 100,
      },
    ];

    if (onUpdateProject) {
      onUpdateProject({ accepted_stories: updatedStories });
    }

    onRunStep("accept_stories", { accepted_stories: updatedStories });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 4000);
  };

  return (
    <div className="space-y-6 max-w-4xl animate-fade-in">
      <div className="flex items-center justify-between border-b border-[#2A262E] pb-4">
        <div>
          <h2 className="text-lg font-bold font-display text-[#ECE7E1] uppercase tracking-wide">
            3. Edición & Pulido del Texto
          </h2>
          <p className="text-xs text-[#8E8780] mt-1">
            Edita el título o el cuerpo de la historia para ajustar la narración y la pronunciación.
          </p>
        </div>

        <Button
          variant="primary"
          icon={Save}
          loading={loading}
          onClick={handleSaveText}
        >
          Guardar Cambios de Texto
        </Button>
      </div>

      {savedSuccess && (
        <CheckAnimation message="¡Texto guardado exitosamente en el proyecto!" />
      )}

      <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-5 shadow-lg">
        {/* Metrics Header */}
        <div className="grid grid-cols-3 gap-3 p-3.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-xs font-mono">
          <div className="flex items-center gap-2 text-[#8E8780]">
            <Type className="w-4 h-4 text-[#E5484D]" />
            <span>Caracteres: <strong className="text-[#ECE7E1]">{charCount}</strong></span>
          </div>
          <div className="flex items-center gap-2 text-[#8E8780]">
            <Edit3 className="w-4 h-4 text-[#E5484D]" />
            <span>Palabras: <strong className="text-[#ECE7E1]">{wordCount}</strong></span>
          </div>
          <div className="flex items-center gap-2 text-[#8E8780]">
            <Clock className="w-4 h-4 text-[#E5484D]" />
            <span>Duración est.: <strong className="text-[#ECE7E1]">~{estimatedSecs}s</strong></span>
          </div>
        </div>

        <Field label="Título de la Historia (Reddit Card Title)">
          <input
            type="text"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              setSavedSuccess(false);
            }}
            className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm font-bold text-[#ECE7E1]"
          />
        </Field>

        <Field label="Contenido Principal (Texto de la Narración)">
          <textarea
            rows={12}
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              setSavedSuccess(false);
            }}
            className="w-full px-4 py-3 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm font-mono text-[#ECE7E1] leading-relaxed resize-y"
          />
        </Field>
      </div>
    </div>
  );
}
