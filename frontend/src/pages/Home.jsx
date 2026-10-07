import React from 'react';
import { Play, ArrowRight, Sparkles } from 'lucide-react';

export default function Home({ onNavigateCreate }) {
    const recentVideos = [
        { id: 1, title: "r/AskReddit - Historias perturbadoras", duration: "0:45", views: "1.2k" },
        { id: 2, title: "r/nosleep - Mi casa no está sola", duration: "1:00", views: "3.4k" },
        { id: 3, title: "r/tifu - Arruiné la cena familiar", duration: "0:30", views: "850" },
    ];

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex flex-col items-center">

            {/* Hero Section */}
            <div className="text-center max-w-3xl my-8 space-y-6">

                {/* Badge "Automatización con IA" */}
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-black ui-badge-ai shadow-sm">
                    <Sparkles className="w-4 h-4" />
                    <span>Automatización con IA</span>
                </div>

                {/* Título Principal */}
                <h1 className="text-4xl sm:text-5xl font-black tracking-tight ui-text-title leading-tight">
                    Convierte historias de Reddit en videos con IA
                </h1>

                {/* Subtítulo */}
                <p className="text-lg font-medium ui-text-sub">
                    Narración automática, escenas generadas por IA y subtítulos listos para compartir en TikTok, Reels y Shorts.
                </p>

                {/* Botón CTA */}
                <div className="pt-2">
                    <button
                        onClick={onNavigateCreate}
                        className="inline-flex items-center gap-2 ui-btn-primary font-bold px-8 py-4 rounded-2xl shadow-lg transition-all transform hover:scale-105 cursor-pointer text-base"
                        type="button"
                    >
                        Crear mi video <ArrowRight className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Galería de Videos Recientes */}
            <div className="w-full mt-12 space-y-6">
                <h2 className="text-2xl font-black ui-text-title">
                    Videos recientes de la comunidad
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {recentVideos.map((item) => (
                        <div
                            key={item.id}
                            className="ui-card rounded-3xl p-6 flex flex-col items-center justify-center min-h-[220px] transition group hover:border-indigo-500"
                        >
                            {/* Botón Play */}
                            <div className="w-14 h-14 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition cursor-pointer">
                                <Play className="w-6 h-6 fill-current ml-0.5" />
                            </div>

                            {/* Título y Detalles del Video */}
                            <div className="mt-5 text-center space-y-1.5 w-full">
                                <p className="text-base font-bold ui-text-title leading-snug">
                                    {item.title}
                                </p>
                                <p className="text-xs font-bold ui-text-sub">
                                    {item.duration} • {item.views} vistas
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

        </div>
    );
}