import React, { useState, useEffect } from 'react';
import { X, Mail, Lock, User } from 'lucide-react';

export default function AuthModal({ isOpen, initialMode = 'login', onClose }) {
    const [mode, setMode] = useState(initialMode);

    useEffect(() => {
        setMode(initialMode);
    }, [initialMode]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center ui-modal-overlay p-4">
            <div className="ui-modal-box relative w-full max-w-md rounded-3xl p-6 sm:p-8 shadow-2xl transition-all">

                {/* Botón Cerrar */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 rounded-full ui-text-sub hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
                    type="button"
                >
                    <X className="w-5 h-5" />
                </button>

                {/* Header */}
                <div className="text-center mb-6">
                    <h2 className="text-2xl font-black ui-text-title">
                        {mode === 'login' ? '¡Bienvenido de nuevo!' : 'Crea tu cuenta'}
                    </h2>
                    <p className="text-sm font-bold ui-text-sub mt-1">
                        {mode === 'login'
                            ? 'Ingresa tus credenciales para continuar'
                            : 'Únete para crear videos de Reddit con IA'}
                    </p>
                </div>

                {/* Formulario */}
                <form onSubmit={(e) => { e.preventDefault(); onClose(); }} className="space-y-4">
                    {mode === 'register' && (
                        <div>
                            <label className="block text-xs font-black uppercase tracking-wider ui-text-title mb-1.5">
                                Nombre de usuario
                            </label>
                            <div className="relative">
                                <User className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 ui-text-sub" />
                                <input
                                    type="text"
                                    placeholder="Tu usuario"
                                    required
                                    className="w-full pl-10 pr-4 py-3 rounded-xl ui-input text-sm font-bold"
                                />
                            </div>
                        </div>
                    )}

                    <div>
                        <label className="block text-xs font-black uppercase tracking-wider ui-text-title mb-1.5">
                            Correo Electrónico
                        </label>
                        <div className="relative">
                            <Mail className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 ui-text-sub" />
                            <input
                                type="email"
                                placeholder="correo@ejemplo.com"
                                required
                                className="w-full pl-10 pr-4 py-3 rounded-xl ui-input text-sm font-bold"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-black uppercase tracking-wider ui-text-title mb-1.5">
                            Contraseña
                        </label>
                        <div className="relative">
                            <Lock className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 ui-text-sub" />
                            <input
                                type="password"
                                placeholder="••••••••"
                                required
                                className="w-full pl-10 pr-4 py-3 rounded-xl ui-input text-sm font-bold"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="w-full ui-btn-primary font-bold py-3.5 rounded-xl shadow-lg transition mt-2 cursor-pointer text-base"
                    >
                        {mode === 'login' ? 'Iniciar Sesión' : 'Registrarse'}
                    </button>
                </form>

                {/* Alternar Modo */}
                <div className="mt-6 text-center text-xs font-bold ui-text-sub">
                    {mode === 'login' ? (
                        <p>
                            ¿No tienes cuenta?{' '}
                            <button
                                onClick={() => setMode('register')}
                                className="text-indigo-600 dark:text-indigo-400 font-extrabold hover:underline cursor-pointer"
                                type="button"
                            >
                                Regístrate aquí
                            </button>
                        </p>
                    ) : (
                        <p>
                            ¿Ya tienes cuenta?{' '}
                            <button
                                onClick={() => setMode('login')}
                                className="text-indigo-600 dark:text-indigo-400 font-extrabold hover:underline cursor-pointer"
                                type="button"
                            >
                                Inicia sesión aquí
                            </button>
                        </p>
                    )}
                </div>

            </div>
        </div>
    );
}