import React, { useState, useEffect } from "react";
import { Key, Video, Save, RefreshCw, Globe, Mic, Sparkles } from "lucide-react";
import Field from "../../components/ui/Field";
import SecretInput from "../../components/ui/SecretInput";
import Button from "../../components/ui/Button";
import {
  fetchSettings,
  updateSettings,
  testServiceCredentials,
  fetchAssets,
} from "../../api/client";

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [assets, setAssets] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [testResults, setTestResults] = useState({
    reddit: null,
    elevenlabs: null,
    openai: null,
  });
  const [testing, setTesting] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sData, aData] = await Promise.all([fetchSettings(), fetchAssets()]);
      setSettings(sData);
      setAssets(aData);
    } catch (e) {
      console.error("Error cargando configuración", e);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (key, val) => {
    setSettings((prev) => ({ ...prev, [key]: val }));
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSettings(settings);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      alert(`Error al guardar: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async (service) => {
    setTesting((prev) => ({ ...prev, [service]: true }));
    try {
      const res = await testServiceCredentials(service);
      setTestResults((prev) => ({ ...prev, [service]: res }));
    } catch (e) {
      setTestResults((prev) => ({
        ...prev,
        [service]: { status: "error", msg: e.message },
      }));
    } finally {
      setTesting((prev) => ({ ...prev, [service]: false }));
    }
  };

  if (loading || !settings) {
    return (
      <div className="p-16 text-center text-[#8E8780]">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[#E5484D]" />
        Cargando configuración y estado de APIs...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-6 space-y-8 pb-16 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#2A262E] pb-5">
        <div>
          <h1 className="text-2xl font-bold font-display text-[#ECE7E1] tracking-wide uppercase">
            Ajustes & Credenciales
          </h1>
          <p className="text-xs text-[#8E8780] mt-1">
            Administra las claves API de Reddit, ElevenLabs, OpenAI y la configuración de render.
          </p>
        </div>
        <Button
          variant="primary"
          icon={Save}
          loading={saving}
          onClick={handleSave}
        >
          {saveSuccess ? "¡Guardado!" : "Guardar Cambios"}
        </Button>
      </div>

      {/* Simplified API Status Pills Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Reddit Status Pill */}
        <div className="bg-[#141217] border border-[#2A262E] rounded-xl p-3 flex items-center justify-between shadow-md">
          <div className="flex items-center gap-2.5">
            <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${
              testResults.reddit?.status === "ok" ? "bg-emerald-400 shadow-[0_0_8px_#34D399]" : "bg-[#5C554E]"
            }`} />
            <div className="flex flex-col">
              <span className="text-xs font-bold text-[#ECE7E1]">Reddit API</span>
              <span className="text-[10px] text-[#8E8780] font-mono">
                {testResults.reddit?.status === "ok" ? "Conectado" : "Sin verificar"}
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            loading={testing.reddit}
            onClick={() => handleTest("reddit")}
            className="text-[11px] px-2 py-1"
          >
            Probar
          </Button>
        </div>

        {/* ElevenLabs Status Pill */}
        <div className="bg-[#141217] border border-[#2A262E] rounded-xl p-3 flex items-center justify-between shadow-md">
          <div className="flex items-center gap-2.5">
            <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${
              testResults.elevenlabs?.status === "ok" ? "bg-emerald-400 shadow-[0_0_8px_#34D399]" : "bg-[#5C554E]"
            }`} />
            <div className="flex flex-col">
              <span className="text-xs font-bold text-[#ECE7E1]">ElevenLabs</span>
              <span className="text-[10px] text-[#8E8780] font-mono">
                {testResults.elevenlabs?.status === "ok" ? "Conectado" : "Sin verificar"}
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            loading={testing.elevenlabs}
            onClick={() => handleTest("elevenlabs")}
            className="text-[11px] px-2 py-1"
          >
            Probar
          </Button>
        </div>

        {/* OpenAI Status Pill */}
        <div className="bg-[#141217] border border-[#2A262E] rounded-xl p-3 flex items-center justify-between shadow-md">
          <div className="flex items-center gap-2.5">
            <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${
              testResults.openai?.status === "ok" ? "bg-emerald-400 shadow-[0_0_8px_#34D399]" : "bg-[#5C554E]"
            }`} />
            <div className="flex flex-col">
              <span className="text-xs font-bold text-[#ECE7E1]">OpenAI</span>
              <span className="text-[10px] text-[#8E8780] font-mono">
                {testResults.openai?.status === "ok" ? "Conectado" : "Sin verificar"}
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            loading={testing.openai}
            onClick={() => handleTest("openai")}
            className="text-[11px] px-2 py-1"
          >
            Probar
          </Button>
        </div>
      </div>

      {/* Reddit API Detailed Config */}
      <section className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-4 shadow-lg">
        <div className="flex items-center justify-between border-b border-[#2A262E]/60 pb-3">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-[#E5484D]" />
            <h2 className="text-sm font-bold text-[#ECE7E1] uppercase tracking-wider">
              Credenciales de Reddit API
            </h2>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Client ID" description="Tu ID de aplicación en reddit.com/prefs/apps">
            <SecretInput
              settingKey="REDDIT_CLIENT_ID"
              value={settings.REDDIT_CLIENT_ID}
              onChange={(v) => handleChange("REDDIT_CLIENT_ID", v)}
            />
          </Field>

          <Field label="Client Secret" description="La contraseña/secreto de tu app de Reddit">
            <SecretInput
              settingKey="REDDIT_CLIENT_SECRET"
              value={settings.REDDIT_CLIENT_SECRET}
              onChange={(v) => handleChange("REDDIT_CLIENT_SECRET", v)}
            />
          </Field>
        </div>

        <Field label="User Agent" description="Identificador enviado a la API de Reddit">
          <input
            type="text"
            value={settings.REDDIT_USER_AGENT || ""}
            onChange={(e) => handleChange("REDDIT_USER_AGENT", e.target.value)}
            className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-sm font-mono text-[#ECE7E1]"
          />
        </Field>
      </section>

      {/* ElevenLabs API Detailed Config */}
      <section className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-4 shadow-lg">
        <div className="flex items-center justify-between border-b border-[#2A262E]/60 pb-3">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-[#E5484D]" />
            <h2 className="text-sm font-bold text-[#ECE7E1] uppercase tracking-wider">
              Credenciales de ElevenLabs (Voz TTS)
            </h2>
          </div>
        </div>

        <Field
          label="API Key Principal"
          description="Llave de ElevenLabs activa para la narración"
        >
          <SecretInput
            settingKey="ELEVENLABS_API_KEYS"
            value={settings.ELEVENLABS_API_KEYS}
            onChange={(v) => handleChange("ELEVENLABS_API_KEYS", v)}
          />
        </Field>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Voice ID por defecto" description="ID de la voz seleccionada en ElevenLabs">
            <input
              type="text"
              value={settings.ELEVENLABS_VOICE_ID || ""}
              onChange={(e) => handleChange("ELEVENLABS_VOICE_ID", e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-sm font-mono text-[#ECE7E1]"
            />
          </Field>

          <Field label="Velocidad de Voz (Speed)" description="Multiplicador de velocidad (ej: 1.1)">
            <input
              type="number"
              step="0.05"
              value={settings.ELEVENLABS_SPEED || 1.1}
              onChange={(e) => handleChange("ELEVENLABS_SPEED", parseFloat(e.target.value))}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-sm font-mono text-[#ECE7E1]"
            />
          </Field>
        </div>
      </section>

      {/* OpenAI API Detailed Config */}
      <section className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-4 shadow-lg">
        <div className="flex items-center justify-between border-b border-[#2A262E]/60 pb-3">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-[#E5484D]" />
            <h2 className="text-sm font-bold text-[#ECE7E1] uppercase tracking-wider">
              Credenciales de OpenAI (GPT-4o + DALL-E 3)
            </h2>
          </div>
        </div>

        <Field label="OpenAI API Key" description="Requerida para la generación de escenas por IA y desinfección de prompts">
          <SecretInput
            settingKey="OPENAI_API_KEY"
            value={settings.OPENAI_API_KEY}
            onChange={(v) => handleChange("OPENAI_API_KEY", v)}
          />
        </Field>
      </section>

      {/* Formatos & Fondos */}
      <section className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-4 shadow-lg">
        <div className="flex items-center gap-2 border-b border-[#2A262E]/60 pb-3">
          <Video className="w-5 h-5 text-[#E5484D]" />
          <h2 className="text-sm font-bold text-[#ECE7E1] uppercase tracking-wider">
            Formatos & Fondos Predeterminados
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Audio Ambiental Predeterminado">
            <select
              value={settings.BACKGROUND_AUDIO || ""}
              onChange={(e) => handleChange("BACKGROUND_AUDIO", e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-sm text-[#ECE7E1]"
            >
              {assets?.background_audios?.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Video de Fondo Clásico Predeterminado">
            <select
              value={settings.BACKGROUND_VIDEO || ""}
              onChange={(e) => handleChange("BACKGROUND_VIDEO", e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-sm text-[#ECE7E1]"
            >
              {assets?.background_videos?.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <div className="grid grid-cols-3 gap-4 pt-2">
          <Field label="Ancho (px)">
            <input
              type="number"
              value={settings.VIDEO_WIDTH || 1080}
              onChange={(e) => handleChange("VIDEO_WIDTH", parseInt(e.target.value))}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-sm font-mono text-[#ECE7E1]"
            />
          </Field>

          <Field label="Alto (px)">
            <input
              type="number"
              value={settings.VIDEO_HEIGHT || 1920}
              onChange={(e) => handleChange("VIDEO_HEIGHT", parseInt(e.target.value))}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-sm font-mono text-[#ECE7E1]"
            />
          </Field>

          <Field label="Volumen Música (dB)">
            <input
              type="number"
              value={settings.BACKGROUND_VOLUME_DB || -18}
              onChange={(e) => handleChange("BACKGROUND_VOLUME_DB", parseFloat(e.target.value))}
              className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-sm font-mono text-[#ECE7E1]"
            />
          </Field>
        </div>
      </section>
    </div>
  );
}
