import React, { useState, useEffect, useRef } from "react";
import { Image as ImageIcon, Video, Sparkles, Edit3, CheckCircle2, Link as LinkIcon, Globe, Check } from "lucide-react";
import Field from "../../components/ui/Field";
import Button from "../../components/ui/Button";
import { fetchAssets, updateProject, getMediaUrl, validateVideoLink } from "../../api/client";

export default function BackgroundStep({ project, onRunStep, loading, onUpdateProject }) {
  const [bgType, setBgType] = useState(project?.background_type || "scenes");
  const [assets, setAssets] = useState(null);
  const [selectedClassicVideo, setSelectedClassicVideo] = useState(project?.background_video_path || "");
  const [startSecond, setStartSecond] = useState(project?.start_second || 0);
  const [classicSourceType, setClassicSourceType] = useState(
    (project?.background_video_path || "").startsWith("http") ? "url" : "local"
  );
  const [videoUrlInput, setVideoUrlInput] = useState(
    (project?.background_video_path || "").startsWith("http") ? project.background_video_path : ""
  );
  const [urlValidating, setUrlValidating] = useState(false);
  const [urlSuccess, setUrlSuccess] = useState(false);

  const [editingSceneNum, setEditingSceneNum] = useState(null);
  const [editedPrompt, setEditedPrompt] = useState("");
  const [cacheBuster, setCacheBuster] = useState(Date.now());

  const videoRef = useRef(null);
  const [videoDuration, setVideoDuration] = useState(0);

  useEffect(() => {
    fetchAssets().then((res) => {
      setAssets(res);
      if (!selectedClassicVideo && res?.background_videos?.length > 0) {
        const defaultVid = res.background_videos[0];
        setSelectedClassicVideo(defaultVid);
        saveBackgroundConfig(bgType, defaultVid, startSecond);
      }
    }).catch(console.error);
  }, []);

  // Update backend project AND local React state immediately
  const saveBackgroundConfig = async (newType, newVideo, newStart) => {
    const typeToSave = newType !== undefined ? newType : bgType;
    const videoToSave = newVideo !== undefined ? newVideo : selectedClassicVideo;
    const startToSave = newStart !== undefined ? newStart : startSecond;

    setBgType(typeToSave);
    if (newVideo !== undefined) setSelectedClassicVideo(newVideo);
    if (newStart !== undefined) setStartSecond(newStart);

    // Sync React state in memory immediately so Render step sees it instantly
    if (onUpdateProject) {
      onUpdateProject({
        background_type: typeToSave,
        background_video_path: videoToSave,
        start_second: startToSave,
      });
    }

    if (project?.id) {
      try {
        await updateProject(project.id, {
          background_type: typeToSave,
          background_video_path: videoToSave,
          start_second: startToSave,
        });
      } catch (err) {
        console.error("Error al guardar configuración de fondo:", err);
      }
    }
  };

  const handlePlanScenes = () => {
    saveBackgroundConfig("scenes", selectedClassicVideo, startSecond);
    onRunStep("plan_scenes", { model: "gpt-image-1" });
  };

  const handleRenderScenes = () => {
    saveBackgroundConfig("scenes", selectedClassicVideo, startSecond);
    onRunStep("render_scenes", { model: "gpt-image-1" });
    setCacheBuster(Date.now());
  };

  const handleRegenerateScene = (sceneNum) => {
    onRunStep("regenerate_scene", {
      scene_number: sceneNum,
      prompt: editedPrompt || undefined,
      model: "gpt-image-1",
    });
    setEditingSceneNum(null);
    setCacheBuster(Date.now());
  };


  const handleApplyVideoUrl = async () => {
    if (!videoUrlInput.trim()) return;
    setUrlValidating(true);
    setUrlSuccess(false);
    try {
      await validateVideoLink(videoUrlInput.trim());
      setSelectedClassicVideo(videoUrlInput.trim());
      saveBackgroundConfig("classic", videoUrlInput.trim(), startSecond);
      setUrlSuccess(true);
      setTimeout(() => setUrlSuccess(false), 3000);
    } catch (e) {
      alert("Error con el enlace de video: " + (e.message || e));
    } finally {
      setUrlValidating(false);
    }
  };

  const handleSetTimeAsStart = () => {
    if (videoRef.current) {
      const sec = Math.floor(videoRef.current.currentTime);
      setStartSecond(sec);
      saveBackgroundConfig("classic", selectedClassicVideo, sec);
    }
  };

  const plan = project?.scenes_plan;
  const scenes = plan?.scenes || [];
  const scenesRendered = project?.scenes_rendered;

  return (
    <div className="space-y-6 w-full max-w-5xl mx-auto animate-fade-in">
      <div className="border-b border-[#2A262E] pb-4">
        <h2 className="text-2xl font-black font-display text-[#ECE7E1] uppercase tracking-wider">
          6. Configuración del Fondo (Escenas IA vs Clásico)
        </h2>
        <p className="text-xs text-[#8E8780] mt-1">
          Elige entre generar escenas visuales 3D con IA o usar un video en bucle de fondo.
        </p>
      </div>

      {/* Background Type Switcher Tabs */}
      <div className="grid grid-cols-2 gap-4">
        <button
          type="button"
          onClick={() => saveBackgroundConfig("scenes")}
          className={`p-5 rounded-2xl border text-left transition-all cursor-pointer relative overflow-hidden ${
            bgType === "scenes"
              ? "bg-[#1E1A24] border-[#E5484D] text-[#ECE7E1] shadow-xl shadow-[#E5484D]/10 scale-[1.01]"
              : "bg-[#141217] border-[#2A262E] text-[#8E8780] hover:border-[#3D3844] hover:text-[#ECE7E1]"
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className={`w-5 h-5 ${bgType === "scenes" ? "text-[#E5484D]" : "text-[#8E8780]"}`} />
            <span className="font-bold text-sm text-[#ECE7E1]">Escenas IA (Recomendado)</span>
          </div>
          <p className="text-xs text-[#8E8780] leading-relaxed">
            GPT-4o analiza la historia y genera imágenes de escenas en estilo visual 3D con animación Ken Burns.
          </p>
          {bgType === "scenes" && (
            <div className="absolute top-0 right-0 w-3 h-3 bg-[#E5484D] rounded-bl-lg" />
          )}
        </button>

        <button
          type="button"
          onClick={() => saveBackgroundConfig("classic")}
          className={`p-5 rounded-2xl border text-left transition-all cursor-pointer relative overflow-hidden ${
            bgType === "classic"
              ? "bg-[#1E1A24] border-[#E5484D] text-[#ECE7E1] shadow-xl shadow-[#E5484D]/10 scale-[1.01]"
              : "bg-[#141217] border-[#2A262E] text-[#8E8780] hover:border-[#3D3844] hover:text-[#ECE7E1]"
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            <Video className={`w-5 h-5 ${bgType === "classic" ? "text-[#E5484D]" : "text-[#8E8780]"}`} />
            <span className="font-bold text-sm text-[#ECE7E1]">Video Clásico</span>
          </div>
          <p className="text-xs text-[#8E8780] leading-relaxed">
            Usa un video de fondo de alta resolución (Minecraft, Subway Surfers, Parkour) recortado dinámicamente.
          </p>
          {bgType === "classic" && (
            <div className="absolute top-0 right-0 w-3 h-3 bg-[#E5484D] rounded-bl-lg" />
          )}
        </button>
      </div>

      {/* Option A: AI Scenes */}
      {bgType === "scenes" && (
        <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-[#2A262E] pb-4">
            <div>
              <h3 className="text-sm font-bold text-[#ECE7E1] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#E5484D]" />
                Generador de Escenas IA (gpt-image-1 / DALL-E 3)
              </h3>
              <p className="text-xs text-[#8E8780] mt-0.5">
                Paso 1: Generar plan de escenas con GPT-4o • Paso 2: Renderizar imágenes PNG
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                loading={loading && !plan}
                onClick={handlePlanScenes}
              >
                {plan ? "Regenerar Plan GPT" : "1. Generar Plan de Escenas"}
              </Button>

              {plan && (
                <Button
                  variant="primary"
                  size="sm"
                  icon={Sparkles}
                  loading={loading}
                  onClick={handleRenderScenes}
                >
                  {scenesRendered ? "Volver a Renderizar Imágenes" : "2. Renderizar Imágenes PNG"}
                </Button>
              )}
            </div>
          </div>

          {/* Visual Bible */}
          {plan?.visual_bible && (
            <div className="p-3 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-xs space-y-1">
              <span className="font-bold text-[#E5484D] uppercase tracking-wider text-[10px]">
                Visual Bible (Estilo Visual del Video):
              </span>
              <p className="text-[#8E8780] font-mono leading-relaxed line-clamp-3">
                {plan.visual_bible}
              </p>
            </div>
          )}

          {/* Live Scenes Grid */}
          {scenes.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-xs font-semibold text-[#ECE7E1] uppercase tracking-wider flex items-center gap-2">
                <span>Escenas del Plan ({scenes.length})</span>
                {scenesRendered && (
                  <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> PNGs Listos
                  </span>
                )}
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {scenes.map((s) => {
                  const isEditing = editingSceneNum === s.scene_number;
                  const subreddit = project?.subreddit || "nosleep";
                  const storyId = project?.accepted_stories?.[0]?.id;
                  const imgUrl = getMediaUrl(`/media/scenes/${subreddit}/${storyId}/scene_${String(s.scene_number).padStart(2, "0")}.png?t=${cacheBuster}`);

                  return (
                    <div
                      key={s.scene_number}
                      className="bg-[#0E0D0F] border border-[#2A262E] rounded-xl p-4 space-y-3 text-xs"
                    >
                      <div className="flex items-center justify-between border-b border-[#2A262E] pb-2">
                        <span className="font-bold font-mono text-[#ECE7E1] flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-[#E5484D]" />
                          Escena #{s.scene_number} ({s.time_start}s - {s.time_end}s)
                        </span>
                        <span className="text-[10px] text-[#8E8780] font-mono bg-[#1A181F] px-2 py-0.5 rounded">
                          {s.narrative_beat}
                        </span>
                      </div>

                      {/* Scene Live Image Preview */}
                      <div className="aspect-[9/16] max-h-56 bg-[#1A181F] rounded-xl border border-[#2A262E] overflow-hidden relative flex items-center justify-center group">
                        <img
                          src={imgUrl}
                          alt={`Escena ${s.scene_number}`}
                          onError={(e) => {
                            e.target.style.display = "none";
                            if (e.target.nextSibling) {
                              e.target.nextSibling.style.display = "flex";
                            }
                          }}
                          onLoad={(e) => {
                            e.target.style.display = "block";
                            if (e.target.nextSibling) {
                              e.target.nextSibling.style.display = "none";
                            }
                          }}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 flex flex-col items-center justify-center p-3 text-center bg-[#141217]">
                          <ImageIcon className="w-8 h-8 text-[#5C554E] mb-2 animate-pulse" />
                          <span className="text-[11px] text-[#8E8780] font-mono font-medium">
                            {loading ? "Generando PNG con IA..." : "PNG pendiente de renderizado"}
                          </span>
                        </div>
                      </div>

                      {isEditing ? (
                        <div className="space-y-2 pt-1">
                          <textarea
                            rows={3}
                            value={editedPrompt}
                            onChange={(e) => setEditedPrompt(e.target.value)}
                            className="w-full p-2 bg-[#1A181F] border border-[#E5484D] rounded-lg font-mono text-[11px] text-[#ECE7E1]"
                          />
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingSceneNum(null)}
                            >
                              Cancelar
                            </Button>
                            <Button
                              variant="primary"
                              size="sm"
                              loading={loading}
                              onClick={() => handleRegenerateScene(s.scene_number)}
                            >
                              Regenerar Escena
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2 pt-1">
                          <p className="text-[11px] text-[#8E8780] font-mono leading-relaxed line-clamp-2">
                            {s.image_prompt}
                          </p>
                          <div className="flex justify-end">
                            <Button
                              variant="secondary"
                              size="sm"
                              icon={Edit3}
                              onClick={() => {
                                setEditingSceneNum(s.scene_number);
                                setEditedPrompt(s.image_prompt);
                              }}
                            >
                              Editar Prompt
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Option B: Classic Video with Preview Player */}
      {bgType === "classic" && (
        <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2 border-b border-[#2A262E] pb-2">
                  <button
                    type="button"
                    onClick={() => setClassicSourceType("local")}
                    className={`px-3 py-1.5 text-xs font-mono font-bold rounded-lg transition-colors cursor-pointer ${
                      classicSourceType === "local"
                        ? "bg-[#E5484D] text-white"
                        : "text-[#8E8780] hover:text-[#ECE7E1]"
                    }`}
                  >
                    Videos del Servidor
                  </button>
                  <button
                    type="button"
                    onClick={() => setClassicSourceType("url")}
                    className={`px-3 py-1.5 text-xs font-mono font-bold rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 ${
                      classicSourceType === "url"
                        ? "bg-[#E5484D] text-white"
                        : "text-[#8E8780] hover:text-[#ECE7E1]"
                    }`}
                  >
                    <Globe className="w-3.5 h-3.5" />
                    Enlace URL (Ahorra Espacio)
                  </button>
                </div>

                {classicSourceType === "local" ? (
                  <Field label="Seleccionar Video de Fondo">
                    <select
                      value={selectedClassicVideo}
                      onChange={(e) => saveBackgroundConfig("classic", e.target.value, startSecond)}
                      className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm font-semibold text-[#ECE7E1]"
                    >
                      {assets?.background_videos?.map((v) => (
                        <option key={v} value={v}>
                          {v}
                        </option>
                      ))}
                    </select>
                  </Field>
                ) : (
                  <Field
                    label="Pegar Enlace Directo a Video MP4"
                    description="No ocupa almacenamiento permanente en el servidor (se descarga temporalmente solo para el renderizado)"
                  >
                    <div className="flex items-center gap-2">
                      <div className="relative flex-1">
                        <LinkIcon className="w-4 h-4 text-[#8E8780] absolute left-3 top-3 pointer-events-none" />
                        <input
                          type="url"
                          value={videoUrlInput}
                          onChange={(e) => setVideoUrlInput(e.target.value)}
                          placeholder="https://ejemplo.com/gameplay.mp4"
                          className="w-full pl-9 pr-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-xs font-mono text-[#ECE7E1]"
                        />
                      </div>
                      <Button
                        variant="primary"
                        size="sm"
                        loading={urlValidating}
                        onClick={handleApplyVideoUrl}
                        className="shrink-0"
                      >
                        {urlSuccess ? <Check className="w-4 h-4" /> : "Usar URL"}
                      </Button>
                    </div>
                  </Field>
                )}
              </div>

              <Field
                label="Segundo de Inicio (start_second)"
                description="Segundo del video donde iniciará el fragmento de fondo"
              >
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="0"
                    max={Math.floor(videoDuration) || 9999}
                    value={startSecond}
                    onChange={(e) => {
                      const val = parseInt(e.target.value) || 0;
                      setStartSecond(val);
                      saveBackgroundConfig("classic", selectedClassicVideo, val);
                    }}
                    className="w-full px-4 py-2.5 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm font-mono text-[#ECE7E1]"
                  />
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleSetTimeAsStart}
                    className="shrink-0"
                  >
                    Usar tiempo actual
                  </Button>
                </div>
              </Field>

              <div className="p-3.5 bg-[#0E0D0F] border border-[#2A262E] rounded-xl text-xs space-y-2 font-mono">
                <div className="flex justify-between text-[#8E8780]">
                  <span>Duración total video:</span>
                  <span className="text-[#ECE7E1]">{Math.floor(videoDuration)}s</span>
                </div>
                <div className="flex justify-between text-[#8E8780]">
                  <span>Punto de inicio elegido:</span>
                  <span className="text-[#E5484D] font-bold">{startSecond}s</span>
                </div>
              </div>
            </div>

            {/* Video Preview Player */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-[#ECE7E1] uppercase tracking-wider block">
                Previsualizador del Video de Fondo
              </label>

              {selectedClassicVideo ? (
                <div className="aspect-[9/16] max-h-72 mx-auto bg-black rounded-xl overflow-hidden border border-[#2A262E] shadow-lg relative">
                  <video
                    ref={videoRef}
                    src={selectedClassicVideo.startsWith("http://") || selectedClassicVideo.startsWith("https://") ? selectedClassicVideo : getMediaUrl(`/media/${selectedClassicVideo}`)}
                    controls
                    onLoadedMetadata={() => {
                      if (videoRef.current) setVideoDuration(videoRef.current.duration);
                    }}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="aspect-[9/16] max-h-72 mx-auto bg-[#0E0D0F] rounded-xl border border-[#2A262E] flex items-center justify-center text-xs text-[#8E8780]">
                  No se seleccionó video
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
