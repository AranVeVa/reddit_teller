import React, { useState } from "react";
import { User, Lock, Mail, X, AlertCircle, CheckCircle2, Send } from "lucide-react";
import Button from "./Button";
import { loginUser, registerUser, resendVerificationEmail } from "../../api/client";

export default function AuthModal({ isOpen, onClose, onAuthSuccess, reason }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [resendState, setResendState] = useState("idle"); // idle | sending | sent

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setNeedsVerification(false);
    setLoading(true);

    try {
      if (isLogin) {
        const res = await loginUser(email, password);
        onAuthSuccess(res.user);
        setPassword("");
        onClose();
      } else {
        // El registro NO inicia sesión: primero hay que confirmar el correo.
        await registerUser(email, password);
        setPassword("");
        setResendState("idle");
        setRegistrationSuccess(true);
      }
    } catch (err) {
      setError(err.message || "Error en la autenticación");
      setNeedsVerification(isLogin && err.status === 403);
    } finally {
      setLoading(false);
    }
  };

  const resetAndClose = () => {
    setRegistrationSuccess(false);
    setNeedsVerification(false);
    setIsLogin(true);
    setEmail("");
    setPassword("");
    setError("");
    onClose();
  };

  const handleResend = async () => {
    setResendState("sending");
    try {
      await resendVerificationEmail(email);
      setResendState("sent");
    } catch (err) {
      setResendState("idle");
      setError(err.message);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-[#141217] border border-[#2A262E] w-full max-w-md rounded-2xl p-6 shadow-2xl relative space-y-5">
        <button
          onClick={resetAndClose}
          className="absolute top-4 right-4 text-[#8E8780] hover:text-[#ECE7E1] p-1 rounded-lg transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {registrationSuccess ? (
          <div className="text-center space-y-4 py-4 animate-fade-in">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center mx-auto mb-2 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
              <Send className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold font-display uppercase tracking-wider text-[#ECE7E1]">
              Revisa tu correo
            </h3>
            <p className="text-sm text-[#8E8780] px-4">
              Hemos enviado un enlace de confirmación a <strong className="text-[#ECE7E1]">{email}</strong>. Haz clic en el enlace para activar tu cuenta antes de iniciar sesión.
            </p>
            <div className="pt-4 space-y-2">
              <Button onClick={() => { setRegistrationSuccess(false); setIsLogin(true); }} variant="secondary" className="w-full justify-center">
                Volver al Inicio de Sesión
              </Button>
              <button
                type="button"
                onClick={handleResend}
                disabled={resendState !== "idle"}
                className="text-xs text-[#8E8780] hover:text-[#ECE7E1] transition-colors cursor-pointer disabled:opacity-60"
              >
                {resendState === "sent" ? "Correo reenviado ✓" : resendState === "sending" ? "Enviando..." : "¿No llegó? Reenviar correo"}
              </button>
            </div>
          </div>
        ) : (
          <>
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
                  : "Mínimo 8 caracteres. Te enviaremos un correo para confirmar tu cuenta."}
              </p>
            </div>

            {reason && !error && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-300">
                {reason}
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-xs text-red-300 space-y-2">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                  <span>{error}</span>
                </div>
                {needsVerification && (
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={resendState !== "idle"}
                    className="underline text-red-200 hover:text-white cursor-pointer disabled:opacity-60"
                  >
                    {resendState === "sent" ? "Correo reenviado ✓" : resendState === "sending" ? "Enviando..." : "Reenviar correo de confirmación"}
                  </button>
                )}
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
                    className="w-full pl-9 pr-4 py-2 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] outline-none rounded-xl text-sm font-mono text-[#ECE7E1]"
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
                    minLength={isLogin ? undefined : 8}
                    autoComplete={isLogin ? "current-password" : "new-password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-4 py-2 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] outline-none rounded-xl text-sm font-mono text-[#ECE7E1]"
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
                  setNeedsVerification(false);
                }}
                className="text-xs text-[#8E8780] hover:text-[#ECE7E1] transition-colors cursor-pointer"
              >
                {isLogin ? "¿No tienes cuenta? Regístrate aquí" : "¿Ya tienes cuenta? Inicia sesión"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}