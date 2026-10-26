import React, { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import { Film, Download, RefreshCw, HardDrive, Play, Mic, Music, Video, Upload, CheckCircle2 } from "lucide-react";
import Button from "../components/ui/Button";
import CheckAnimation from "../components/ui/CheckAnimation";
import { fetchLibrary, uploadMediaFile, getMediaUrl } from "../api/client";

export default function LibraryPage() {
  const [libraryData, setLibraryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccessMsg, setUploadSuccessMsg] = useState("");
  const [activeTab, setActiveTab] = useState("produced_videos");
  const [selectedItem, setSelectedItem] = useState(null);

  const fileInputRef = useRef(null);

  const categories = [
    { id: "produced_videos", label: "Videos Renderizados", icon: Film, canUpload: false },
    { id: "elevenlabs_audios", label: "Voces ElevenLabs", icon: Mic, canUpload: false },
    { id: "mixed_audios", label: "Audios Mezclados", icon: Music, canUpload: false },
    {
      id: "background_videos",
      label: "Videos de Fondo",
      icon: Video,
      canUpload: true,
      uploadType: "background_video",
      uploadLabel: "Subir Video",
      accept: ".mp4,.mov,.mkv"
    },
    {
      id: "background_audios",
      label: "Música Ambiental",
      icon: Music,
      canUpload: true,
      uploadType: "background_audio",
      uploadLabel: "Subir Audio",
      accept: ".mp3,.wav,.aac"
    },
  ];

  useEffect(() => {
    loadLibrary();
  }, []);

  const loadLibrary = async () => {
    setLoading(true);
    try {
      const data = await fetchLibrary();
      setLibraryData(data);
      const initialItems = data[activeTab] || [];
      if (initialItems.length > 0) {
        setSelectedItem(initialItems[0]);
      } else {
        setSelectedItem(null);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (catId) => {
    setActiveTab(catId);
    const items = libraryData?.[catId] || [];
    setSelectedItem(items.length > 0 ? items[0] : null);
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const currentCatObj = categories.find((c) => c.id === activeTab);
    if (!currentCatObj || !currentCatObj.canUpload) return;

    setUploading(true);
    setUploadSuccessMsg("");

    try {
      const res = await uploadMediaFile(currentCatObj.uploadType, file);
      setUploadSuccessMsg(`¡Archivo "${file.name}" subido con éxito!`);
      setTimeout(() => setUploadSuccessMsg(""), 5000);
      await loadLibrary();
    } catch (err) {
      alert(`Error al subir archivo: ${err.message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  if (loading || !libraryData) {
    return (
      <div className="p-16 text-center text-[#8E8780]">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[#E5484D]" />
        Cargando biblioteca multimedia...
      </div>
    );
  }

  const currentItems = libraryData[activeTab] || [];
  const currentCatObj = categories.find((c) => c.id === activeTab);

  return (
    <div className="w-full py-8 pb-16 animate-fade-in space-y-6">
      {/* Top Header Container */}
      <div className="max-w-6xl mx-auto px-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-black font-display text-[#ECE7E1] tracking-wider uppercase">
                BIBLIOTECA
              </h1>
              <span className="w-2.5 h-2.5 rounded-full bg-[#E5484D]" />
            </div>
            <p className="text-xs text-[#8E8780] mt-1 font-sans">
              Explora todos tus videos renderizados, narraciones, audios mezclados y gestiona tu contenido multimedia.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {currentCatObj?.canUpload && (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={currentCatObj.accept}
                  onChange={handleFileChange}
                  className="hidden"
                />
                <button
                  type="button"
                  disabled={uploading}
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#9F1D20] hover:bg-[#B3261E] active:scale-[0.98] text-white text-xs font-bold font-mono uppercase tracking-wider rounded-xl border border-[#E5484D]/30 transition-all cursor-pointer disabled:opacity-50 shrink-0"
                >
                  {uploading ? (
                    <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  ) : (
                    <Upload className="w-4 h-4 text-white" />
                  )}
                  <span>{currentCatObj.uploadLabel}</span>
                </button>
              </>
            )}

            <Button variant="secondary" icon={RefreshCw} onClick={loadLibrary}>
              Actualizar
            </Button>
          </div>
        </div>

        {uploadSuccessMsg && (
          <CheckAnimation message={uploadSuccessMsg} />
        )}
      </div>

      {/* Full-Width Divider Tabs Sector - 100% Screen Width Always */}
      <div className="w-full border-b border-[#2A262E] py-1 bg-[#141217]/40 shadow-sm">
        <div className="w-full grid grid-cols-2 sm:grid-cols-5 divide-x divide-[#2A262E]/70 items-center">
          {categories.map((c) => {
            const Icon = c.icon;
            const isActive = activeTab === c.id;
            const count = libraryData[c.id]?.length || 0;

            return (
              <button
                key={c.id}
                type="button"
                onClick={() => handleTabChange(c.id)}
                className="relative w-full px-3 py-3.5 flex flex-col items-center justify-center text-center transition-all cursor-pointer select-none group"
              >
                <div className="flex items-center gap-2 mb-1 z-10">
                  <Icon className={`w-4 h-4 transition-colors duration-200 ${isActive ? "text-[#E5484D]" : "text-[#8E8780] group-hover:text-[#ECE7E1]"}`} />
                  <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-full transition-colors duration-200 ${
                    isActive ? "bg-[#9F1D20] text-white" : "bg-[#0E0D0F] text-[#8E8780]"
                  }`}>
                    {count}
                  </span>
                </div>

                <div className="relative z-10 flex items-center justify-center w-full">
                  <span
                    className="text-xs font-bold tracking-wider uppercase transition-colors duration-200"
                    style={{ color: isActive ? "#E5484D" : "#8E8780" }}
                  >
                    {c.label}
                  </span>

                  {isActive && (
                    <motion.span
                      layoutId="activeLibraryTabRedText"
                      className="absolute inset-0 text-xs font-black tracking-wider uppercase text-[#E5484D] pointer-events-none drop-shadow-[0_0_8px_rgba(229,72,77,0.5)] flex items-center justify-center"
                      transition={{ type: "spring", stiffness: 450, damping: 32 }}
                    >
                      {c.label}
                    </motion.span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Media Items Content Container */}
      <div className="max-w-6xl mx-auto px-6 space-y-6">
        {currentItems.length === 0 ? (
        <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-16 text-center space-y-4">
          <Film className="w-10 h-10 text-[#5C554E] mx-auto" />
          <div className="space-y-1">
            <h3 className="text-base font-medium text-[#ECE7E1]">
              No hay archivos en esta categoría aún
            </h3>
            <p className="text-xs text-[#8E8780] max-w-sm mx-auto">
              {currentCatObj?.canUpload
                ? `Haz clic en "${currentCatObj.uploadLabel}" para añadir tu propio archivo.`
                : "Genera recursos desde el Estudio de Producción para verlos organizados aquí."}
            </p>
          </div>

          {currentCatObj?.canUpload && (
            <button
              type="button"
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#9F1D20] hover:bg-[#E5484D] text-white text-xs font-bold font-mono uppercase tracking-wider rounded-xl shadow-lg transition-all cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              <span>{currentCatObj.uploadLabel} Ahora</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Media Player */}
          <div className="lg:col-span-2 space-y-4">
            {selectedItem && (
              <div className="bg-[#141217] border border-[#2A262E] rounded-2xl overflow-hidden p-5 space-y-4 shadow-xl">
                {selectedItem.type === "video" ? (
                  <div className="aspect-[9/16] max-h-[520px] mx-auto bg-[#0E0D0F] rounded-xl overflow-hidden border border-[#2A262E] shadow-2xl">
                    <video
                      key={selectedItem.path}
                      src={getMediaUrl(`/media/${selectedItem.path}`)}
                      controls
                      autoPlay
                      className="w-full h-full object-contain"
                    />
                  </div>
                ) : (
                  <div className="p-8 bg-[#0E0D0F] rounded-xl border border-[#2A262E] space-y-6 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#9F1D20]/20 border border-[#E5484D]/40 flex items-center justify-center mx-auto text-[#E5484D]">
                      <Music className="w-8 h-8" />
                    </div>
                    <div className="space-y-1">
                      <h3 className="text-sm font-bold font-mono text-[#ECE7E1]">
                        {selectedItem.name}
                      </h3>
                      <p className="text-xs text-[#8E8780] font-mono">
                        Ruta: {selectedItem.path}
                      </p>
                    </div>
                    <audio
                      key={selectedItem.path}
                      src={getMediaUrl(`/media/${selectedItem.path}`)}
                      controls
                      autoPlay
                      className="w-full accent-[#E5484D]"
                    />
                  </div>
                )}

                <div className="flex items-center justify-between pt-3 border-t border-[#2A262E]">
                  <div>
                    <h2 className="text-sm font-bold text-[#ECE7E1] font-mono truncate max-w-md">
                      {selectedItem.name}
                    </h2>
                    <p className="text-xs text-[#8E8780] flex items-center gap-2 mt-0.5 font-mono">
                      <HardDrive className="w-3.5 h-3.5 text-[#E5484D]" />
                      {selectedItem.size_mb} MB • {selectedItem.category}
                    </p>
                  </div>

                  <a
                    href={getMediaUrl(`/media/${selectedItem.path}`)}
                    download={selectedItem.name}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#9F1D20] hover:bg-[#B3261E] text-[#ECE7E1] text-xs font-bold rounded-xl shadow-lg shadow-[#9F1D20]/30 transition-all cursor-pointer shrink-0"
                  >
                    <Download className="w-4 h-4" />
                    Descargar
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* Media List Sidebar */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-[#ECE7E1] uppercase tracking-wider">
              Archivos Disponibles ({currentItems.length})
            </h3>
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1 custom-scrollbar">
              {currentItems.map((item) => {
                const isSelected = selectedItem?.path === item.path;
                return (
                  <div
                    key={item.path}
                    onClick={() => setSelectedItem(item)}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between group ${
                      isSelected
                        ? "bg-[#232029] border-[#E5484D] text-[#ECE7E1] shadow-md shadow-[#E5484D]/10"
                        : "bg-[#141217] border-[#2A262E] hover:border-[#3D3844] text-[#8E8780] hover:text-[#ECE7E1]"
                    }`}
                  >
                    <div className="space-y-1 truncate pr-2">
                      <p className="text-xs font-mono font-bold truncate">
                        {item.name}
                      </p>
                      <p className="text-[10px] font-mono opacity-75">
                        {item.size_mb} MB
                      </p>
                    </div>
                    <Play className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${isSelected ? "text-[#E5484D]" : ""}`} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
    </div>
  );
}

