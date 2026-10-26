import React, { useState, useEffect } from "react";
import { X, CreditCard, Sparkles, ShieldCheck, Check, AlertCircle } from "lucide-react";
import { getPaymentConfig, createCheckout, simulatePayment } from "../../api/client";

export default function PaymentModal({ isOpen, onClose, onPaymentSuccess }) {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!isOpen) return;
        setError("");
        getPaymentConfig().then(setConfig).catch((err) => setError(err.message));
    }, [isOpen]);

    if (!isOpen) return null;

    const handleStripeCheckout = async () => {
        setError("");
        setLoading(true);
        try {
            const { url } = await createCheckout();
            window.location.href = url;              // redirect a Stripe
        } catch (err) {
            setError(err.message || "No se pudo iniciar el pago");
            setLoading(false);
        }
    };

    const handleSimulated = async (outcome) => {
        setError("");
        setLoading(true);
        try {
            const { user } = await simulatePayment(outcome);
            onPaymentSuccess(user);
            onClose();
        } catch (err) {
            setError(err.message || "Pago simulado falló");
        } finally {
            setLoading(false);
        }
    };

    const mode = config?.mode || "simulated";

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
            <div className="bg-[#141217] border border-[#2A262E] w-full max-w-md rounded-2xl p-6 shadow-2xl relative space-y-5">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-[#8E8780] hover:text-[#ECE7E1] p-1 rounded-lg transition-colors cursor-pointer"
                >
                    <X className="w-5 h-5" />
                </button>

                <div className="text-center space-y-2">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-yellow-300 text-[#141217] flex items-center justify-center mx-auto shadow-lg shadow-amber-500/20">
                        <Sparkles className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-black font-display uppercase tracking-wider text-[#ECE7E1]">
                        Plan Pro Reddit Teller
                    </h3>
                    <p className="text-xs text-[#8E8780]">
                        Desbloquea escenas 3D ilimitadas con GPT-4o, DALL-E 3 y exportación en alta calidad.
                    </p>
                </div>

                <div className="bg-[#0E0D0F] border border-[#2A262E] rounded-xl p-4 flex items-center justify-between">
                    <div>
                        <span className="text-xs font-bold text-[#ECE7E1] block">Suscripción Mensual Pro</span>
                        <span className="text-[10px] text-[#8E8780]">Acceso completo inmediato</span>
                    </div>
                    <div className="text-right">
                        <span className="text-lg font-black text-amber-400">
                            ${config ? config.price_usd.toFixed(2) : "9.99"}
                        </span>
                        <span className="text-[10px] text-[#8E8780] block">/{config?.interval || "mes"}</span>
                    </div>
                </div>

                {error && (
                    <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                        <span>{error}</span>
                    </div>
                )}

                {mode === "stripe" ? (
                    <button
                        type="button"
                        onClick={handleStripeCheckout}
                        disabled={loading}
                        className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-[#141217] font-extrabold rounded-xl text-xs uppercase tracking-wider transition-all shadow-lg shadow-amber-500/20 cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {loading ? (
                            <span>Redirigiendo a Stripe...</span>
                        ) : (
                            <>
                                <CreditCard className="w-4 h-4" /> Pagar con Stripe
                            </>
                        )}
                    </button>
                ) : (
                    <div className="space-y-2">
                        <p className="text-[10px] text-[#8E8780] text-center">
                            Modo simulado (sin Stripe configurado)
                        </p>
                        <button
                            type="button"
                            onClick={() => handleSimulated("approved")}
                            disabled={loading}
                            className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-[#141217] font-extrabold rounded-xl text-xs uppercase tracking-wider transition-all shadow-lg shadow-amber-500/20 cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            <Check className="w-4 h-4" /> Simular pago aprobado
                        </button>
                        <button
                            type="button"
                            onClick={() => handleSimulated("rejected")}
                            disabled={loading}
                            className="w-full py-2 bg-[#1E1A24] hover:bg-[#2A2433] text-[#E5484D] border border-[#E5484D]/30 rounded-xl text-xs font-mono uppercase tracking-wider cursor-pointer disabled:opacity-50"
                        >
                            Simular pago rechazado
                        </button>
                    </div>
                )}

                <div className="flex items-center justify-center gap-2 text-[10px] text-[#8E8780]">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>
                        {mode === "stripe"
                            ? "Pago seguro procesado por Stripe (modo test)"
                            : "Simulación local — sin cargos reales"}
                    </span>
                </div>
            </div>
        </div>
    );
}