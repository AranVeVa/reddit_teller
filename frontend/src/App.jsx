import React, { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "motion/react";
import Navbar from "./components/Navbar";
import StudioPage from "./pages/studio/StudioPage";
import LibraryPage from "./pages/LibraryPage";
import SettingsPage from "./pages/settings/SettingsPage";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AuthModal from "./components/ui/AuthModal";
import PaymentModal from "./components/ui/PaymentModal";
import LandingPage from "./pages/LandingPage";
import {
  verifyEmailToken,
  resendVerificationEmail,
  fetchCurrentUser,
  fetchStorageStatus,
  confirmCheckout,
  logoutUser,
} from "./api/client";
import { CheckCircle2, AlertCircle, Loader2, Send } from "lucide-react";

const viewComponents = {
  studio: StudioPage,
  library: LibraryPage,
  settings: SettingsPage,
  admin: AdminDashboard,
};

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [storage, setStorage] = useState(null);

  const [currentTab, setCurrentTab] = useState("studio");
  const prevTabRef = useRef("studio");
  // Dentro de App():
  const [isGuest, setIsGuest] = useState(false);
  // ── Verificación de correo ─────────────────────────────────────────────
  const [verificationToken, setVerificationToken] = useState(null);
  const [verificationStatus, setVerificationStatus] = useState("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const [resendEmail, setResendEmail] = useState("");
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccessMessage, setResendSuccessMessage] = useState("");

  // ── Modales ────────────────────────────────────────────────────────────
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isPaymentOpen, setIsPaymentOpen] = useState(false);
  const [pendingPayment, setPendingPayment] = useState(false);

  // ── Restaurar sesión al cargar ─────────────────────────────────────────
  useEffect(() => {
    const token = typeof localStorage !== "undefined" ? localStorage.getItem("rt_token") : null;
    if (!token) return;
    fetchCurrentUser()
      .then((res) => {
        if (res.authenticated && res.user) setCurrentUser(res.user);
      })
      .catch(() => { });
  }, []);

  // ── Verificación de email en URL (?token=...) ──────────────────────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (token) {
      setVerificationToken(token);
      verifyEmailToken(token)
        .then(() => setVerificationStatus("success"))
        .catch((err) => {
          setVerificationStatus("error");
          setErrorMessage(err.message || "El enlace ha expirado o no es válido.");
        });
    }
  }, []);

  // ── Redirect de Stripe (?payment=success&session_id=cs_test_...) ───────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const payment = params.get("payment");
    const sessionId = params.get("session_id");

    if (payment === "success" && sessionId) {
      confirmCheckout(sessionId)
        .then((res) => {
          if (res.user) setCurrentUser(res.user);
          window.history.replaceState({}, document.title, window.location.pathname);
        })
        .catch((err) => {
          alert(err.message || "No pudimos confirmar el pago. Contacta soporte.");
          window.history.replaceState({}, document.title, window.location.pathname);
        });
    } else if (payment === "cancelled") {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // ── Storage (para el indicador del Navbar) ─────────────────────────────
  useEffect(() => {
    if (!currentUser) return;   // storage requiere auth en algunos casos
    fetchStorageStatus().then(setStorage).catch(() => { });
  }, [currentUser]);

  const handleTabChange = (newTab) => {
    prevTabRef.current = currentTab;
    setCurrentTab(newTab);
  };

  const handleCloseVerification = () => {
    window.history.replaceState({}, document.title, window.location.pathname);
    setVerificationToken(null);
  };

  const handleResend = async (e) => {
    e.preventDefault();
    if (!resendEmail) return;
    setResendLoading(true);
    setResendSuccessMessage("");
    setErrorMessage("");

    try {
      const res = await resendVerificationEmail(resendEmail);
      setResendSuccessMessage(res.message || "Nuevo enlace enviado exitosamente.");
    } catch (err) {
      setErrorMessage(err.message || "Fallo al solicitar el reenvío del correo.");
    } finally {
      setResendLoading(false);
    }
  };

  const handleLoginClick = () => setIsAuthOpen(true);

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
    setStorage(null);
  };

  const handleUpgradeRequest = () => {
    if (!currentUser || !currentUser.email) {
      setPendingPayment(true);
      setIsAuthOpen(true);
    } else {
      setIsPaymentOpen(true);
    }
  };

  const handleAuthSuccess = (user) => {
    setCurrentUser(user);
    setIsAuthOpen(false);
    if (pendingPayment) {
      setTimeout(() => setIsPaymentOpen(true), 300);
      setPendingPayment(false);
    }
  };

  const handlePaymentSuccess = (updatedUser) => {
    setCurrentUser(updatedUser);
    setIsPaymentOpen(false);
    // Refresca storage/estado del usuario desde el backend por si acaso
    fetchCurrentUser()
      .then((res) => {
        if (res.authenticated && res.user) setCurrentUser(res.user);
      })
      .catch(() => { });
  };

  const ActiveView = viewComponents[currentTab];

  // Si no hay usuario y no es invitado, mostramos la presentación
  if (!currentUser && !isGuest) {
    return (
      <LandingPage
        onAuthSuccess={(user) => setCurrentUser(user)}
        onGuestClick={() => setIsGuest(true)}
      />
    );
  }
  
  // Vista aislada para la verificación de correo
  if (verificationToken) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: "#0E0D0F", color: "#ECE7E1" }}>
        <div className="bg-[#141217] border border-[#2A262E] w-full max-w-md rounded-2xl p-8 shadow-2xl text-center space-y-6 animate-fade-in">
          {verificationStatus === "loading" && (
            <>
              <Loader2 className="w-12 h-12 text-[#E5484D] animate-spin mx-auto" />
              <h2 className="text-xl font-bold font-display uppercase tracking-wider">Verificando Correo...</h2>
              <p className="text-sm text-[#8E8780]">Validando token de seguridad con la base de datos...</p>
            </>
          )}

          {verificationStatus === "success" && (
            <>
              <CheckCircle2 className="w-16 h-16 text-emerald-400 mx-auto drop-shadow-[0_0_10px_rgba(52,211,153,0.4)]" />
              <h2 className="text-xl font-bold font-display uppercase tracking-wider">¡Cuenta Verificada!</h2>
              <p className="text-sm text-[#8E8780]">Tu correo ha sido confirmado exitosamente. Ya puedes acceder al panel.</p>
              <button
                onClick={handleCloseVerification}
                className="w-full py-3 bg-[#E5484D] hover:bg-[#B3261E] text-white font-bold rounded-xl transition-colors cursor-pointer"
              >
                Ir al Estudio
              </button>
            </>
          )}

          {verificationStatus === "error" && (
            <>
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto" />
              <h2 className="text-xl font-bold font-display uppercase tracking-wider text-red-400">Enlace Inválido o Expirado</h2>
              <p className="text-xs text-[#8E8780]">{errorMessage}</p>

              {resendSuccessMessage ? (
                <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-xs text-emerald-300">
                  {resendSuccessMessage}
                </div>
              ) : (
                <form onSubmit={handleResend} className="space-y-3 pt-2 text-left">
                  <label className="text-[10px] font-mono text-[#8E8780] uppercase block">Ingresa tu correo para solicitar otro enlace:</label>
                  <input
                    type="email"
                    required
                    placeholder="tu@email.com"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0E0D0F] border border-[#2A262E] focus:border-[#E5484D] outline-none rounded-xl text-xs font-mono text-[#ECE7E1]"
                  />
                  <button
                    type="submit"
                    disabled={resendLoading}
                    className="w-full py-2.5 bg-[#2A262E] hover:bg-[#38333E] text-xs font-bold rounded-xl transition-colors cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {resendLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4 text-[#E5484D]" />}
                    Reenviar Correo de Confirmación
                  </button>
                </form>
              )}

              <button
                onClick={handleCloseVerification}
                className="text-xs text-[#8E8780] hover:text-[#ECE7E1] underline transition-colors cursor-pointer block mx-auto pt-2"
              >
                Volver al inicio
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden" style={{ backgroundColor: "#0E0D0F", color: "#ECE7E1" }}>
      <Navbar
        currentTab={currentTab}
        setCurrentTab={handleTabChange}
        currentUser={currentUser}
        onLoginClick={handleLoginClick}
        onLogout={handleLogout}
        onUpgradeRequest={handleUpgradeRequest}
        storage={storage}
      />

      <div className="flex-1 relative overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentTab}
            initial={{ opacity: 0, scale: 0.985 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.985 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            className="h-full"
            style={{ backgroundColor: "#0E0D0F" }}
          >
            <ActiveView currentUser={currentUser} onUpgradeRequest={handleUpgradeRequest} />
          </motion.div>
        </AnimatePresence>
      </div>

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => { setIsAuthOpen(false); setPendingPayment(false); }}
        onAuthSuccess={handleAuthSuccess}
      />

      <PaymentModal
        isOpen={isPaymentOpen}
        onClose={() => setIsPaymentOpen(false)}
        onPaymentSuccess={handlePaymentSuccess}
      />
    </div>
  );
}