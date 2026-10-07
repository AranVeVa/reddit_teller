import React from 'react';
import { ArrowLeft, Download, Share2, Sparkles } from 'lucide-react';

export default function VideoResult({ resultData, onReset }) {
    const videoUrl = resultData?.videoUrl || "https://assets.mixkit.co/videos/preview/mixkit-tree-branches-in-the-breeze-1188-large.mp4";

    return (
        <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
            <button
                onClick={onReset}
                className="inline-flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition"
            >
                <ArrowLeft className="w-4 h-4" /> Crear otro video
            </button>

            <div className="text-center space-y-2">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300 border border-green-300 dark:border-green-800">
                    <Sparkles className="w-3.5 h-3.5" /> ¡Video generado con éxito!
                </span>
                <h1 className="text-3xl font-black text-slate-900 dark:text-white">
                    {resultData?.subreddit || 'r/AskReddit'} — Tu video está listo
                </h1>
            </div>

            <div className="card-container bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-3xl p-6 shadow-xl grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                {/* Previsualización del Video */}
                <div className="flex justify-center bg-black rounded-2xl overflow-hidden aspect-[9/16] max-h-[450px] shadow-lg">
                    <video src={videoUrl} controls className="w-full h-full object-cover" />
                </div>

                {/* Detalles y Descarga */}
                <div className="space-y-6">
                    <div className="space-y-2">
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Configuración del render</h3>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                            <strong className="text-slate-900 dark:text-slate-200">Subreddit:</strong> {resultData?.subreddit || 'r/nosleep'}
                        </p>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                            <strong className="text-slate-900 dark:text-slate-200">Orden:</strong> {resultData?.order || 'Top'}
                        </p>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                            <strong className="text-slate-900 dark:text-slate-200">Duración:</strong> {resultData?.duration || 'Corto'}
                        </p>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3 pt-2">
                        <a
                            href={videoUrl}
                            download
                            className="flex-1 inline-flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-xl shadow-md transition"
                        >
                            <Download className="w-4 h-4" /> Descargar MP4
                        </a>
                        <button
                            onClick={() => navigator.clipboard.writeText(window.location.href)}
                            className="inline-flex items-center justify-center gap-2 border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold py-3 px-4 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition"
                        >
                            <Share2 className="w-4 h-4" /> Compartir
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}