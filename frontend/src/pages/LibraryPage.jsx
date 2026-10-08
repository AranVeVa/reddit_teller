import React, { useState, useEffect, useRef } from "react";
import { Film, Download, RefreshCw, HardDrive, Play, Mic, Music, Video, Upload, CheckCircle2 } from "lucide-react";
import Button from "../components/ui/Button";
import CheckAnimation from "../components/ui/CheckAnimation";
import { fetchLibrary, uploadMediaFile } from "../api/client";

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
    { id: "background_videos", label: "Videos de Fondo", icon: Video, canUpload: true, uploadType: "background_video", accept: ".mp4,.mov,.mkv" },
    { id: "background_audios", label: "Música Ambiental", icon: Music, canUpload: true, uploadType: "background_audio", accept: ".mp3,.wav,.aac" },
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
      setUploadSuccessMsg(`¡Archivo "${file.name}" subido con éxito y listo para usar en el Paso 6!`);
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
    <div className="max-w-6xl mx-auto py-8 px-6 space-y-8 pb-16 animate-fade-in">
      <div className="flex items-center justify-between border-b border-[#2A262E] pb-5">
        <div>
          <h1 className="text-2xl font-bold font-display text-[#ECE7E1] tracking-wide uppercase">
            Biblioteca Multimedia Integral
          </h1>
          <p className="text-xs text-[#8E8780] mt-1">
            Explora todos los videos renderizados, narraciones, audios mezclados y sube tus propios videos/música de fondo.
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
              <Button
                variant="primary"
                icon={Upload}
                loading={uploading}
                onClick={() => fileInputRef.current?.click()}
              >
                Subir {currentCatObj.label}
              </Button>
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

      {/* Category Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 custom-scrollbar">
        {categories.map((c) => {
          const Icon = c.icon;
          const isActive = activeTab === c.id;
          const count = libraryData[c.id]?.length || 0;

          return (
            <button
              key={c.id}
              type="button"
              onClick={() => handleTabChange(c.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer select-none border whitespace-nowrap ${
                isActive
                  ? "bg-[#232029] text-[#ECE7E1] border-[#E5484D] shadow-lg shadow-[#E5484D]/10 scale-[1.02]"
                  : "bg-[#141217] text-[#8E8780] border-[#2A262E] hover:border-[#3D3844] hover:text-[#ECE7E1]"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-[#E5484D]" : "text-[#8E8780]"}`} />
              <span>{c.label}</span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                isActive ? "bg-[#9F1D20] text-white" : "bg-[#0E0D0F] text-[#8E8780]"
              }`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {currentItems.length === 0 ? (
        <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-16 text-center space-y-4">
          <Film className="w-10 h-10 text-[#5C554E] mx-auto" />
          <div className="space-y-1">
            <h3 className="text-base font-medium text-[#ECE7E1]">
              No hay archivos en esta categoría aún
            </h3>
            <p className="text-xs text-[#8E8780] max-w-sm mx-auto">
              {currentCatObj?.canUpload
                ? `Haz clic en "Subir ${currentCatObj.label}" para añadir tu propio archivo.`
                : "Genera recursos desde el Estudio de Producción para verlos organizados aquí."}
            </p>
          </div>

          {currentCatObj?.canUpload && (
            <Button
              variant="primary"
              icon={Upload}
              onClick={() => fileInputRef.current?.click()}
            >
              Subir Archivo Ahora
            </Button>
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
                      src={`/media/${selectedItem.path}`}
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
                      src={`/media/${selectedItem.path}`}
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
                    href={`/media/${selectedItem.path}`}
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
  );
}
