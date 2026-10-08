import React, { useState, useEffect } from "react";
import { Mic, Music, Volume2, CheckCircle2 } from "lucide-react";
import Field from "../../components/ui/Field";
import Button from "../../components/ui/Button";
import { fetchAssets } from "../../api/client";

export default function VoiceStep({ project, onRunStep, loading }) {
  const [assets, setAssets] = useState(null);
  const [bgAudio, setBgAudio] = useState(project?.voice_result?.background_audio || "");

  useEffect(() => {
    fetchAssets().then(setAssets).catch(console.error);
  }, []);

  const handleGenerateVoice = () => {
    onRunStep("generate_voice", {});
  };

  const handleMixAudio = () => {
    onRunStep("mix_audio", { background_audio_path: bgAudio || undefined });
  };

  const voiceDone = Boolean(project?.voice_result?.audio_path);
  const mixDone = Boolean(project?.mixed_result?.mixed_audio_path);

  return (
    <div className="space-y-6 w-full max-w-5xl mx-auto animate-fade-in">
      <div className="border-b border-[#2A262E] pb-4">
        <h2 className="text-2xl font-black font-display text-[#ECE7E1] uppercase tracking-wider">
          4. Síntesis de Voz (ElevenLabs) & Mezcla
        </h2>
        <p className="text-xs text-[#8E8780] mt-1">
          Genera la locución con la API de ElevenLabs y mézclala con la música ambiental de fondo.
        </p>
      </div>

      {/* Step 4A: Voice TTS */}
      <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-[#2A262E] pb-3">
          <div className="flex items-center gap-2">
            <Mic className="w-5 h-5 text-[#E5484D]" />
            <h3 className="text-sm font-bold text-[#ECE7E1]">
              Paso 4A: Narración de Voz (ElevenLabs)
            </h3>
          </div>

          <Button
            variant={voiceDone ? "secondary" : "primary"}
            loading={loading && !voiceDone}
            onClick={handleGenerateVoice}
          >
            {voiceDone ? "Regenerar Voz" : "Generar Voz con ElevenLabs"}
          </Button>
        </div>

        {voiceDone && (
          <div className="p-4 bg-[#0E0D0F] border border-[#2A262E] rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs text-emerald-400 font-mono flex items-center gap-2 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Narración generada con éxito ({Math.round(project.voice_result.duration || 0)}s)
              </p>
              <span className="text-[10px] font-mono text-[#8E8780]">Solo Voz</span>
            </div>
            <audio
              src={`/media/${project.voice_result.audio_path}`}
              controls
              className="w-full h-10 accent-[#E5484D]"
            />
          </div>
        )}
      </div>

      {/* Step 4B: Audio Mixing */}
      {voiceDone && (
        <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-4 animate-fade-in">
          <div className="flex items-center justify-between border-b border-[#2A262E] pb-3">
            <div className="flex items-center gap-2">
              <Music className="w-5 h-5 text-[#E5484D]" />
              <h3 className="text-sm font-bold text-[#ECE7E1]">
                Paso 4B: Mezcla de Música Ambiental
              </h3>
            </div>

            <Button
              variant="primary"
              icon={Volume2}
              loading={loading}
              onClick={handleMixAudio}
            >
              {mixDone ? "Volver a Mezclar Audio" : "Mezclar Narración con Música"}
            </Button>
          </div>

          <Field label="Pista de Música Ambiental">
            <select
              value={bgAudio}
              onChange={(e) => setBgAudio(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm text-[#ECE7E1]"
            >
              <option value="">(Por defecto: background_audio/Initiation.mp3)</option>
              {assets?.background_audios?.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </Field>

          {mixDone && (
            <div className="p-4 bg-[#0E0D0F] border border-[#2A262E] rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs text-emerald-400 font-mono flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Audio Mezclado Listo para Video
                </p>
                <span className="text-[10px] font-mono text-[#E5484D] font-bold">Voz + Música</span>
              </div>
              <audio
                src={`/media/${project.mixed_result.mixed_audio_path}`}
                controls
                className="w-full h-10 accent-[#E5484D]"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
