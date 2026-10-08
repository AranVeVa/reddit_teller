import React from 'react';
import { Video, Sun, Moon, PlusCircle, Home } from 'lucide-react';

export default function Navbar({ currentView, setCurrentView, isDarkMode, setIsDarkMode, onOpenAuth }) {
    const handleNav = (view) => {
        setCurrentView(view);
    };

    return (
        <nav className="ui-navbar sticky top-0 z-40 transition-colors">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">

                    {/* Logo */}
                    <div
                        className="flex items-center gap-2.5 cursor-pointer select-none"
                        onClick={() => handleNav('home')}
                    >
                        <div className="bg-indigo-600 p-2 rounded-xl text-white shadow-md">
                            <Video className="w-5 h-5" />
                        </div>
                        <span className="font-black text-xl tracking-tight ui-text-title">
                            Reddit Teller
                        </span>
                    </div>

                    {/* Enlaces de Navegación */}
                    <div className="flex items-center gap-5">
                        <button
                            onClick={() => handleNav('home')}
                            className={`flex items-center gap-1.5 text-sm font-bold transition cursor-pointer ${currentView === 'home'
                                    ? 'text-indigo-600 dark:text-indigo-400 font-extrabold'
                                    : 'ui-nav-text-muted hover:text-indigo-600'
                                }`}
                        >
                            <Home className="w-4 h-4" /> Inicio
                        </button>

                        <button
                            onClick={() => handleNav('create')}
                            className={`flex items-center gap-1.5 text-sm font-bold transition cursor-pointer ${currentView === 'create'
                                    ? 'text-indigo-600 dark:text-indigo-400 font-extrabold'
                                    : 'ui-nav-text-muted hover:text-indigo-600'
                                }`}
                        >
                            <PlusCircle className="w-4 h-4" /> Crear Video
                        </button>

                        <div className="h-4 w-px bg-slate-300 dark:bg-slate-700 mx-1"></div>

                        {/* Switch de Tema */}
                        <button
                            onClick={() => setIsDarkMode(!isDarkMode)}
                            className="p-2 rounded-xl ui-btn-secondary transition cursor-pointer"
                            title="Cambiar Modo"
                            type="button"
                        >
                            {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
                        </button>

                        {/* Login / Register */}
                        <button
                            onClick={() => onOpenAuth('login')}
                            className="text-sm font-bold ui-nav-text hover:text-indigo-600 transition cursor-pointer"
                            type="button"
                        >
                            Iniciar sesión
                        </button>
                        <button
                            onClick={() => onOpenAuth('register')}
                            className="ui-btn-primary text-sm font-bold px-4 py-2 rounded-xl shadow-md transition cursor-pointer"
                            type="button"
                        >
                            Registrarme
                        </button>
                    </div>

                </div>
            </div>
        </nav>
    );
}