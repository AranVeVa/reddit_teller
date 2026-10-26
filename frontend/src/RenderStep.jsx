import React from "react";
import { Play, Volume2, Info, Image as ImageIcon } from "lucide-react";

export default function PreviewPanel({ project }) {
  const selectedStory = project?.accepted_stories?.[0] || project?.candidates?.[0];
  const subreddit = project?.subreddit || "nosleep";
  const darkCard = project?.dark_mode ?? True;

  return (
    <aside className="w-80 bg-[#17151A] border-l border-[#2E2A31] p-4 space-y-4 shrink-0 overflow-y-auto hidden xl:block">
      <div className="flex items-center justify-between border-b border-[#2E2A31] pb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[#ECE7E1]">
          Vista Previa 9:16
        </h3>
        <span className="text-[10px] font-mono bg-[#211E24] border border-[#2E2A31] px-2 py-0.5 rounded text-[#A39C96]">
          1080x1920
        </span>
      </div>

      {/* 9:16 Visual Simulator Card */}
      <div className="aspect-[9/16] bg-[#0E0D0F] border border-[#2E2A31] rounded-xl overflow-hidden relative shadow-lg flex flex-col justify-center p-4">
        {/* Background placeholder or scene preview */}
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900/80 via-purple-950/20 to-slate-950 flex items-center justify-center pointer-events-none">
          <ImageIcon className="w-12 h-12 text-[#2E2A31]" />
        </div>

        {/* Reddit Card Simulation */}
        <div
          className={`relative z-10 p-4 rounded-xl border shadow-xl space-y-3 transition-colors ${
            darkCard
              ? "bg-[#1E1B24] border-[#3730a3]/40 text-[#ECE7E1]"
              : "bg-white text-slate-900 border-slate-200"
          }`}
        >
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-[#E5484D] flex items-center justify-center text-[10px] font-bold text-white">
              r/
            </div>
            <div>
              <p className="text-xs font-bold leading-none">r/{subreddit}</p>
              <p className="text-[9px] opacity-60">u/reddit_teller • hace 3h</p>
            </div>
          </div>

          <p className="text-xs font-bold line-clamp-3 leading-snug">
            {selectedStory ? selectedStory.title : "Título de la historia de Reddit..."}
          </p>

          <div className="flex items-center gap-3 text-[10px] opacity-75 border-t pt-2 border-current/10">
            <span>▲ 2.4k</span>
            <span>💬 184 comentarios</span>
          </div>
        </div>

        {/* Subtitle Card Simulation */}
        <div className="absolute bottom-16 left-4 right-4 text-center z-10">
          <span className="bg-black/80 backdrop-blur-sm text-white text-xs font-bold px-3 py-1.5 rounded border border-white/20 font-display tracking-wide uppercase">
            [ SUBTÍTULOS ANIMADOS ]
          </span>
        </div>
      </div>

      {/* Summary Metadata */}
      <div className="bg-[#211E24] border border-[#2E2A31] rounded-xl p-3 space-y-2 text-xs">
        <div className="flex justify-between text-[#A39C96]">
          <span>Historias Aceptadas:</span>
          <span className="font-mono text-[#ECE7E1]">{project?.accepted_stories?.length || 0}</span>
        </div>
        <div className="flex justify-between text-[#A39C96]">
          <span>Duración Estimada:</span>
          <span className="font-mono text-[#ECE7E1]">
            {project?.voice_result?.duration
              ? `${Math.round(project.voice_result.duration)}s`
              : "~60s"}
          </span>
        </div>
        <div className="flex justify-between text-[#A39C96]">
          <span>Fondo:</span>
          <span className="font-mono text-[#ECE7E1] capitalize">
            {project?.background_type || "Escenas IA"}
          </span>
        </div>
      </div>
    </aside>
  );
}
