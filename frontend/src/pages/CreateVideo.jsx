import React, { useState } from 'react';
import { Loader2, ArrowRight } from 'lucide-react';

export default function CreateVideo({ onGenerated }) {
    const [subreddit, setSubreddit] = useState('r/nosleep');
    const [order, setOrder] = useState('mas-relevantes');
    const [duration, setDuration] = useState('corto');
    const [cardMode, setCardMode] = useState('relevante');
    const [loading, setLoading] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        setLoading(true);

        setTimeout(() => {
            setLoading(false);
            onGenerated({
                subreddit,
                order,
                duration,
                videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-tree-branches-in-the-breeze-1188-large.mp4'
            });
        }, 2500);
    };

    return (
        <div className="max-w-2xl mx-auto px-4 py-12">
            <div className="text-center mb-8 space-y-2">
                <h1 className="text-3xl font-black ui-text-title">
                    Cuéntanos qué video quieres crear
                </h1>
                <p className="text-sm font-bold ui-text-sub">
                    Ajusta las opciones para que el pipeline procese la historia
                </p>
            </div>

            <form onSubmit={handleSubmit} className="ui-card rounded-3xl p-6 sm:p-8 space-y-6">

                {/* Subreddit */}
                <div>
                    <label className="block text-sm font-black ui-text-title mb-2">
                        Subreddit
                    </label>
                    <input
                        type="text"
                        value={subreddit}
                        onChange={(e) => setSubreddit(e.target.value)}
                        required
                        placeholder="ej. r/AskReddit"
                        className="w-full ui-input rounded-xl px-4 py-3 font-bold text-sm"
                    />
                </div>

                {/* Orden */}
                <div>
                    <label className="block text-sm font-black ui-text-title mb-2">
                        Orden de publicaciones
                    </label>
                    <select
                        value={order}
                        onChange={(e) => setOrder(e.target.value)}
                        className="w-full ui-input rounded-xl px-4 py-3 font-bold text-sm"
                    >
                        <option value="mas-relevantes">Más relevantes (Top)</option>
                        <option value="recientes">Recientes (New)</option>
                        <option value="tendencia">En tendencia (Hot)</option>
                    </select>
                </div>

                {/* Duración */}
                <div>
                    <label className="block text-sm font-black ui-text-title mb-2">
                        Duración del video
                    </label>
                    <select
                        value={duration}
                        onChange={(e) => setDuration(e.target.value)}
                        className="w-full ui-input rounded-xl px-4 py-3 font-bold text-sm"
                    >
                        <option value="corto">Corto (~30 segundos)</option>
                        <option value="medio">Medio (~60 segundos)</option>
                        <option value="largo">Largo (~90 segundos)</option>
                    </select>
                </div>

                {/* Modo Tarjeta */}
                <div>
                    <label className="block text-sm font-black ui-text-title mb-2">
                        Modo de tarjeta de Reddit
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                        <button
                            type="button"
                            onClick={() => setCardMode('crear')}
                            className={`py-3 px-4 rounded-xl font-bold text-sm transition cursor-pointer ${cardMode === 'crear'
                                    ? 'ui-btn-primary'
                                    : 'ui-btn-secondary'
                                }`}
                        >
                            Crear
                        </button>
                        <button
                            type="button"
                            onClick={() => setCardMode('relevante')}
                            className={`py-3 px-4 rounded-xl font-bold text-sm transition cursor-pointer ${cardMode === 'relevante'
                                    ? 'ui-btn-primary'
                                    : 'ui-btn-secondary'
                                }`}
                        >
                            Relevante
                        </button>
                    </div>
                </div>

                {/* Botón */}
                <div className="pt-2">
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full ui-btn-primary font-bold py-4 rounded-2xl flex items-center justify-center gap-2 shadow-lg transition disabled:opacity-50 cursor-pointer text-base"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" /> Procesando video e IA...
                            </>
                        ) : (
                            <>
                                Generar mi video <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </div>

            </form>
        </div>
    );
}