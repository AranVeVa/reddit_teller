
import React, { useState } from "react";
import { Film, Sparkles, ShieldCheck, Mail, Lock, UserPlus, LogIn, Mic, Image, Type } from "lucide-react";
import { loginUser, registerUser } from "../api/client";

export default function LandingPage({ onAuthSuccess, onGuestClick }) {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [needsVerification, setNeedsVerification] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setNeedsVerification(false);
        setLoading(true);

        try {
            if (isLogin) {
                const res = await loginUser(email, password);
                onAuthSuccess(res.user);
            } else {
                await registerUser(email, password);
                setError("Cuenta creada. Revisa tu correo para confirmarla.");
                setIsLogin(true);
            }
        } catch (err) {
            setError(err.message || "Error en la autenticación");
            if (isLogin && err.status === 403) setNeedsVerification(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full flex bg-[#0E0D0F] text-[#ECE7E1] font-sans selection:bg-[#E5484D]/30">

            {/* ── Columna Izquierda: Branding y Hero ── */}
            <div className="hidden lg:flex flex-1 flex-col justify-center px-12 xl:px-24 relative overflow-hidden">
                {/* Adorno de fondo */}
                <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-[#E5484D]/10 via-[#0E0D0F] to-[#0E0D0F] z-0"></div>

                <div className="relative z-10 space-y-6">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-12 h-12 rounded-xl bg-[#9F1D20] flex items-center justify-center shadow-lg shadow-[#E5484D]/20">
                            <Film className="w-6 h-6 text-white" />
                        </div>
                        <span className="font-black text-2xl tracking-widest">REDDIT_TELLER</span>
                    </div>

                    <h1 className="text-5xl xl:text-6xl font-black leading-tight font-display">
                        De Reddit a <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#E5484D] to-[#F27A7D]">
                            TikTok en minutos.
                        </span>
                    </h1>
                    <p className="text-lg text-[#8E8780] max-w-lg">
                        La plataforma definitiva para extraer historias virales, generar voces con IA y renderizar videos verticales automáticamente.
                    </p>

                    <div className="flex gap-4 pt-4">
                        <div className="flex items-center gap-2 text-sm text-[#A39C96]">
                            <Sparkles className="w-4 h-4 text-[#E5484D]" /> IA Integrada
                        </div>
                        <div className="flex items-center gap-2 text-sm text-[#A39C96]">
                            <Mic className="w-4 h-4 text-[#E5484D]" /> Voces ElevenLabs
                        </div>
                        <div className="flex items-center gap-2 text-sm text-[#A39C96]">
                            <Image className="w-4 h-4 text-[#E5484D]" /> Escenas DALL-E 3
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Columna Central: Formulario de Login ── */}
            <div className="flex-1 flex items-center justify-center p-6 lg:p-12 z-10">
                <div className="w-full max-w-md bg-[#141217] border border-[#2A262E] rounded-3xl p-8 shadow-2xl relative">

                    <div className="text-center mb-8">
                        <h2 className="text-2xl font-bold font-display uppercase tracking-wider mb-2">
                            {isLogin ? "Bienvenido de nuevo" : "Crea tu cuenta"}
                        </h2>
                        <p className="text-sm text-[#8E8780]">
                            {isLogin ? "Ingresa tus credenciales para acceder a tu estudio." : "Regístrate para empezar a crear videos."}
                        </p>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-xs text-red-300 text-center">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-xs font-mono text-[#8E8780]">Correo Electrónico</label>
                            <div className="relative flex items-center">
                                <Mail className="w-4 h-4 text-[#8E8780] absolute left-3" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="tu@email.com"
                                    className="w-full pl-9 pr-4 py-3 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] outline-none rounded-xl text-sm font-mono transition-colors"
                                />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-mono text-[#8E8780]">Contraseña</label>
                            <div className="relative flex items-center">
                                <Lock className="w-4 h-4 text-[#8E8780] absolute left-3" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className="w-full pl-9 pr-4 py-3 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] outline-none rounded-xl text-sm font-mono transition-colors"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 mt-4 bg-[#E5484D] hover:bg-[#B3261E] text-white font-bold rounded-xl transition-all shadow-lg shadow-[#E5484D]/20 flex justify-center items-center gap-2"
                        >
                            {loading ? "Procesando..." : (isLogin ? <><LogIn className="w-5 h-5" /> Entrar al Estudio</> : <><UserPlus className="w-5 h-5" /> Registrarme</>)}
                        </button>
                    </form>

                    <div className="mt-6 text-center space-y-4">
                        <button
                            onClick={() => { setIsLogin(!isLogin); setError(""); }}
                            className="text-xs text-[#8E8780] hover:text-[#ECE7E1] transition-colors"
                        >
                            {isLogin ? "¿No tienes cuenta? Regístrate aquí" : "¿Ya tienes cuenta? Inicia sesión"}
                        </button>
                        <div className="relative flex items-center justify-center">
                            <div className="border-t border-[#2A262E] w-full absolute"></div>
                            <span className="bg-[#141217] px-2 text-[10px] font-mono text-[#8E8780] relative z-10 uppercase">O</span>
                        </div>
                        <button
                            onClick={onGuestClick}
                            className="text-xs font-bold text-[#E5484D] hover:text-[#F27A7D] transition-colors"
                        >
                            Continuar como Invitado
                        </button>
                    </div>
                </div>
            </div>

            {/* ── Columna Derecha: Características / Roles ── */}
            <div className="hidden xl:flex w-80 flex-col justify-center pr-12 z-10">
                <div className="bg-[#141217]/50 border border-[#2A262E] rounded-2xl p-6 space-y-6">
                    <div>
                        <h3 className="text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-[#E5484D]" /> Características Pro
                        </h3>
                        <ul className="space-y-3 text-sm text-[#8E8780]">
                            <li className="flex gap-2 items-start"><div className="w-1.5 h-1.5 rounded-full bg-[#E5484D] mt-1.5 shrink-0" /> Extracción ilimitada</li>
                            <li className="flex gap-2 items-start"><div className="w-1.5 h-1.5 rounded-full bg-[#E5484D] mt-1.5 shrink-0" /> Voces realistas IA</li>
                            <li className="flex gap-2 items-start"><div className="w-1.5 h-1.5 rounded-full bg-[#E5484D] mt-1.5 shrink-0" /> Subtítulos automáticos</li>
                            <li className="flex gap-2 items-start"><div className="w-1.5 h-1.5 rounded-full bg-[#E5484D] mt-1.5 shrink-0" /> Renderizado 9:16 HD</li>
                        </ul>
                    </div>
                    <div className="border-t border-[#2A262E] pt-6">
                        <h3 className="text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2">
                            <Type className="w-4 h-4 text-[#E5484D]" /> Roles del Sistema
                        </h3>
                        <ul className="space-y-2 text-xs">
                            <li className="flex justify-between items-center"><span className="text-[#ECE7E1]">Super Admin</span> <span className="text-[10px] bg-red-900/30 text-red-400 px-2 py-0.5 rounded">Total</span></li>
                            <li className="flex justify-between items-center"><span className="text-[#ECE7E1]">Usuario Pro</span> <span className="text-[10px] bg-amber-900/30 text-amber-400 px-2 py-0.5 rounded">Premium</span></li>
                            <li className="flex justify-between items-center"><span className="text-[#ECE7E1]">Usuario Free</span> <span className="text-[10px] bg-gray-800 text-gray-400 px-2 py-0.5 rounded">Básico</span></li>
                        </ul>
                    </div>
                </div>
            </div>

        </div>
    );
}