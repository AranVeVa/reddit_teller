import React, { useState } from "react";
import { User, Lock, Mail, X, Check, AlertCircle } from "lucide-react";
import Button from "./Button";
import { loginUser, registerUser } from "../../api/client";

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isLogin) {
        const res = await loginUser(email, password);
        onAuthSuccess(res.user);
      } else {
        const res = await registerUser(email, password);
        onAuthSuccess(res.user);
      }
      onClose();
    } catch (err) {
      setError(err.message || "Error en la autenticación");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-[#141217] border border-[#2A262E] w-full max-w-md rounded-2xl p-6 shadow-2xl relative space-y-5">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#8E8780] hover:text-[#ECE7E1] p-1 rounded-lg transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center space-y-1">
          <div className="w-12 h-12 rounded-xl bg-[#9F1D20]/20 border border-[#E5484D]/40 text-[#E5484D] flex items-center justify-center mx-auto mb-3">
            <User className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold font-display uppercase tracking-wider text-[#ECE7E1]">
            {isLogin ? "Iniciar Sesión" : "Crear Cuenta"}
          </h3>
          <p className="text-xs text-[#8E8780]">
            {isLogin
              ? "Accede a tus historias y videos en la nube de Neon"
              : "Regístrate para guardar tus proyectos en tu base de datos"}
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-mono text-[#8E8780]">Correo Electrónico</label>
            <div className="relative flex items-center">
              <Mail className="w-4 h-4 text-[#8E8780] absolute left-3 pointer-events-none" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@email.com"
                className="w-full pl-9 pr-4 py-2 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm font-mono text-[#ECE7E1]"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono text-[#8E8780]">Contraseña</label>
            <div className="relative flex items-center">
              <Lock className="w-4 h-4 text-[#8E8780] absolute left-3 pointer-events-none" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-4 py-2 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] rounded-xl text-sm font-mono text-[#ECE7E1]"
              />
            </div>
          </div>

          <Button type="submit" variant="primary" loading={loading} className="w-full justify-center">
            {isLogin ? "Entrar" : "Registrarme"}
          </Button>
        </form>

        <div className="text-center pt-2 border-t border-[#2A262E]">
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
            }}
            className="text-xs text-[#8E8780] hover:text-[#ECE7E1] transition-colors cursor-pointer"
          >
            {isLogin ? "¿No tienes cuenta? Regístrate aquí" : "¿Ya tienes cuenta? Inicia sesión"}
          </button>
        </div>
      </div>
    </div>
  );
}
