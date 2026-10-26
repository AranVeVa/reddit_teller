import { useState, useEffect, useCallback, useRef } from "react";
import { fetchStorageStatus, triggerStorageCleanup } from "../api/client";

/**
 * Estado compartido del almacenamiento (/api/storage/status) con sondeo cada 30 s
 * y acción de limpieza (/api/storage/cleanup).
 */
export default function useStorage() {
  const [stats, setStats] = useState(null);
  const [cleaning, setCleaning] = useState(false);
  const [message, setMessage] = useState(null);
  const timer = useRef(null);

  const refresh = useCallback(async () => {
    try {
      setStats(await fetchStorageStatus());
    } catch (_) { }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const flash = (msg) => {
    setMessage(msg);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setMessage(null), 5000);
  };

  const cleanup = useCallback(async () => {
    setCleaning(true);
    try {
      const res = await triggerStorageCleanup();
      flash(res.cleaned ? `Liberados ${res.freed_mb} MB (${res.deleted_count} archivos)` : "No había nada que limpiar");
      await refresh();
    } catch (e) {
      flash(e.status === 401 ? "Inicia sesión para limpiar el almacenamiento" : e.message);
    } finally {
      setCleaning(false);
    }
  }, [refresh]);

  return { stats, cleaning, message, cleanup, refresh };
}
