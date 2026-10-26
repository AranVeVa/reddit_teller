import React, { useEffect, useState } from "react";
import { X, Sparkles, CreditCard, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { fetchPaymentConfig, createCheckoutSession, simulatePayment } from "../../api/client";

/**
 * Modal de suscripción Pro ($9.99/mes).
 *  - mode "stripe":    redirige a Stripe Checkout (modo test con tarjeta 4242 4242 4242 4242).
 *  - mode "simulator": aprueba / rechaza el pago en el backend, que actualiza is_premium y role en Neon.
 */
export default function PaymentModal({ isOpen, onClose, onSuccess }) {
  const [config, setConfig] = useState(null);
  const [busy, setBusy] = useState(null); // "approved" | "rejected" | "stripe"
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setError("");
    setDone(false);
    fetchPaymentConfig().then(setConfig).catch(() => setConfig({ mode: "simulator", price_label: "$9.99" }));
  }, [isOpen]);

  if (!isOpen) return null;

  const price = config?.price_label || "$9.99";
  const isStripe = config?.mode === "stripe";

  const payStripe = async () => {
    setBusy("stripe");
    setError("");
    try {
      const { url } = await createCheckoutSession();
      window.location.href = url;
    } catch (e) {
      setError(e.message);
      setBusy(null);
    }
  };

  const paySimulated = async (outcome) => {
    setBusy(outcome);
    setError("");
    try {
      const res = await simulatePayment(outcome);
      setDone(true);
      setTimeout(() => onSuccess?.(res.user), 900);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in p-4">
      <div className="bg-[#141217] border border-[#2A262E] rounded-2xl p-8 max-w-md w-full shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-[#8E8780] hover:text-[#ECE7E1] cursor-pointer">
          <X className="w-5 h-5" />
        </button>

        {done ? (
          <div className="text-center space-y-4 py-6">
            <CheckCircle2 className="w-16 h-16 text-emerald-400 mx-auto drop-shadow-[0_0_10px_rgba(52,211,153,0.5)]" />
            <h3 className="text-xl font-black text-[#ECE7E1] uppercase">¡Bienvenido a Pro!</h3>
            <p className="text-sm text-[#8E8780]">Escenas IA y renderizado premium desbloqueados.</p>
          </div>
        ) : (
          <>
            <div className="text-center space-y-4 mb-8">
              <div className="w-16 h-16 bg-gradient-to-tr from-amber-500 to-yellow-300 rounded-2xl mx-auto flex items-center justify-center shadow-lg">
                <Sparkles className="w-8 h-8 text-[#141217]" />
              </div>
              <h3 className="text-xl font-black text-[#ECE7E1] uppercase">Suscripción Pro</h3>
              <p className="text-sm text-[#8E8780]">
                Estás a un paso de desbloquear la Generación IA (GPT-4o + DALL-E 3) y el Renderizado Premium.
              </p>
              <div className="text-3xl font-bold text-amber-400">
                {price} <span className="text-sm text-[#8E8780] font-normal">/mes</span>
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{error}</span>
              </div>
            )}

            {!config ? (
              <div className="flex justify-center py-4"><Loader2 className="w-6 h-6 animate-spin text-[#E5484D]" /></div>
            ) : isStripe ? (
              <>
                <button
                  onClick={payStripe}
                  disabled={!!busy}
                  className="w-full py-3 px-4 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white font-bold rounded-xl text-sm transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-70 cursor-pointer"
                >
                  {busy ? <Loader2 className="w-5 h-5 animate-spin" /> : <CreditCard className="w-5 h-5" />}
                  {busy ? "Redirigiendo a Stripe..." : "Pagar con Tarjeta"}
                </button>
                <p className="text-[10px] text-center text-[#6E6760] font-mono mt-3">
                  Modo prueba · tarjeta 4242 4242 4242 4242, cualquier fecha futura y CVC
                </p>
              </>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-center gap-2 text-[10px] font-mono text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg py-1.5">
                  <AlertCircle className="w-3 h-3" /> MODO SIMULADOR · no se realiza ningún cobro
                </div>
                <button
                  onClick={() => paySimulated("approved")}
                  disabled={!!busy}
                  className="w-full py-3 px-4 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white font-bold rounded-xl text-sm transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-70 cursor-pointer"
                >
                  {busy === "approved" ? <Loader2 className="w-5 h-5 animate-spin" /> : <CreditCard className="w-5 h-5" />}
                  {busy === "approved" ? "Procesando pago..." : `Pagar ${price} (simular aprobado)`}
                </button>
                <button
                  onClick={() => paySimulated("rejected")}
                  disabled={!!busy}
                  className="w-full py-2.5 px-4 bg-transparent border border-[#2A262E] hover:bg-[#2A262E] text-[#8E8780] hover:text-[#ECE7E1] font-semibold rounded-xl text-xs transition-all disabled:opacity-70 cursor-pointer"
                >
                  Simular pago rechazado
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
