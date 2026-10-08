import React, { useState } from "react";
import { Eye, EyeOff, Copy, Check, Lock } from "lucide-react";
import { revealSetting } from "../../api/client";

export default function SecretInput({
  settingKey,
  value,
  onChange,
  placeholder = "sk-...",
  disabled = false,
}) {
  const [showSecret, setShowSecret] = useState(false);
  const [revealedValue, setRevealedValue] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleToggleReveal = async () => {
    if (showSecret) {
      setShowSecret(false);
      return;
    }

    if (revealedValue !== null) {
      setShowSecret(true);
      return;
    }

    setLoading(true);
    try {
      const res = await revealSetting(settingKey);
      setRevealedValue(res.value || "");
      setShowSecret(true);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    const valToCopy = revealedValue !== null ? revealedValue : value;
    if (valToCopy) {
      navigator.clipboard.writeText(valToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const displayValue = showSecret
    ? (revealedValue !== null ? revealedValue : value)
    : value;

  return (
    <div className="relative flex items-center">
      <div className="absolute left-3 text-[#6E6760] pointer-events-none">
        <Lock className="w-4 h-4" />
      </div>

      <input
        type={showSecret ? "text" : "password"}
        value={displayValue || ""}
        onChange={(e) => {
          setRevealedValue(e.target.value);
          onChange(e.target.value);
        }}
        disabled={disabled}
        placeholder={placeholder}
        className="w-full pl-9 pr-20 py-2 bg-[#17151A] border border-[#2E2A31] focus:border-[#E5484D] rounded-lg text-[#ECE7E1] font-mono text-sm placeholder-[#6E6760] transition-colors"
      />

      <div className="absolute right-2 flex items-center gap-1">
        <button
          type="button"
          onClick={handleToggleReveal}
          disabled={disabled || loading}
          aria-pressed={showSecret}
          title={showSecret ? "Ocultar clave" : "Revelar clave"}
          className="p-1.5 text-[#A39C96] hover:text-[#ECE7E1] hover:bg-[#2B272F] rounded transition-colors cursor-pointer"
        >
          {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>

        <button
          type="button"
          onClick={handleCopy}
          title="Copiar al portapapeles"
          className="p-1.5 text-[#A39C96] hover:text-[#ECE7E1] hover:bg-[#2B272F] rounded transition-colors cursor-pointer"
        >
          {copied ? (
            <Check className="w-4 h-4 text-emerald-400" />
          ) : (
            <Copy className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  );
}
