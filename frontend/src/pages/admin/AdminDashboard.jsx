import React, { useState, useEffect } from "react";
import { Users, Mail, Crown, ShieldCheck, Edit2, X, Loader2, Save, Calendar } from "lucide-react";
import { apiRequest } from "../../api/client"; // Ajusta la ruta si es necesario

export default function AdminDashboard() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // Estados para el modal de edición
    const [selectedUser, setSelectedUser] = useState(null);
    const [editRole, setEditRole] = useState("Usuario");
    const [editPremium, setEditPremium] = useState(false);
    const [saving, setSaving] = useState(false);

    // Cargar usuarios de la base de datos
    const fetchUsers = async () => {
        try {
            setLoading(true);
            const data = await apiRequest("/admin/users");
            setUsers(data.users || []);
        } catch (err) {
            setError(err.message || "Error al cargar los usuarios");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleEditClick = (user) => {
        setSelectedUser(user);
        setEditRole(user.role || "Usuario");
        setEditPremium(user.is_premium || false);
    };

    const handleSave = async () => {
        if (!selectedUser) return;
        setSaving(true);
        try {
            await apiRequest(`/admin/users/${selectedUser.id}`, {
                method: "PATCH",
                body: JSON.stringify({ role: editRole, is_premium: editPremium }),
            });

            // Actualizar la tabla visualmente sin recargar la página
            setUsers(users.map(u =>
                u.id === selectedUser.id ? { ...u, role: editRole, is_premium: editPremium } : u
            ));
            setSelectedUser(null); // Cerrar modal
        } catch (err) {
            alert(err.message || "Error al guardar los cambios");
        } finally {
            setSaving(false);
        }
    };

    // Formatear la fecha de registro (viene de Neon)
    const formatDate = (dateString) => {
        if (!dateString) return "N/A";
        const date = new Date(dateString);
        return date.toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric' });
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-full min-h-[50vh]">
                <Loader2 className="w-8 h-8 text-[#E5484D] animate-spin" />
            </div>
        );
    }

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fade-in">

            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-black font-display uppercase tracking-wider text-[#ECE7E1] flex items-center gap-2">
                        <Users className="w-6 h-6 text-[#E5484D]" />
                        Gestión de Usuarios y Roles
                    </h1>
                    <p className="text-sm text-[#8E8780] mt-1">
                        Administra los accesos, roles y suscripciones de la plataforma.
                    </p>
                </div>
                <span className="bg-[#141217] text-[#E5484D] text-sm font-mono px-4 py-2 rounded-xl border border-[#2A262E]">
                    Total: {users.length} registrados
                </span>
            </div>

            {error && (
                <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-xl text-sm text-red-300">
                    {error}
                </div>
            )}

            {/* Tabla de Usuarios */}
            <div className="bg-[#141217] border border-[#2A262E] rounded-2xl overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#0E0D0F] text-[#8E8780] text-[10px] uppercase font-mono tracking-wider">
                                <th className="p-4 border-b border-[#2A262E]">Usuario (Email)</th>
                                <th className="p-4 border-b border-[#2A262E]">Rol</th>
                                <th className="p-4 border-b border-[#2A262E]">Suscripción</th>
                                <th className="p-4 border-b border-[#2A262E]">Estado</th>
                                <th className="p-4 border-b border-[#2A262E]">Fecha de Alta</th>
                                <th className="p-4 border-b border-[#2A262E] text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#2A262E]">
                            {users.map((u) => (
                                <tr key={u.id} className="hover:bg-[#1A171D] transition-colors">
                                    <td className="p-4 text-sm font-mono text-[#ECE7E1] flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-[#2A262E] flex items-center justify-center text-[#E5484D]">
                                            <Mail className="w-4 h-4" />
                                        </div>
                                        {u.email}
                                    </td>
                                    <td className="p-4">
                                        <span className={`text-[10px] font-bold px-2 py-1 rounded-md border uppercase tracking-wider ${u.role === "Super Admin"
                                                ? "bg-[#9F1D20]/20 text-[#E5484D] border-[#E5484D]/40"
                                                : "bg-[#232029] text-[#8E8780] border-[#2A262E]"
                                            }`}>
                                            {u.role || "Usuario"}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        {u.is_premium ? (
                                            <span className="flex items-center gap-1.5 text-amber-400 text-xs font-bold bg-amber-500/10 px-2 py-1 rounded-md border border-amber-500/20 w-fit">
                                                <Crown className="w-3.5 h-3.5" /> PRO
                                            </span>
                                        ) : (
                                            <span className="text-[#8E8780] text-xs font-mono">FREE</span>
                                        )}
                                    </td>
                                    <td className="p-4">
                                        {u.is_verified ? (
                                            <span className="text-emerald-400 text-xs font-bold flex items-center gap-1.5">
                                                <ShieldCheck className="w-4 h-4" /> Verificado
                                            </span>
                                        ) : (
                                            <span className="text-red-400 text-xs font-bold">Pendiente</span>
                                        )}
                                    </td>
                                    <td className="p-4 text-xs font-mono text-[#8E8780]">
                                        <span className="flex items-center gap-1.5">
                                            <Calendar className="w-3.5 h-3.5" />
                                            {formatDate(u.created_at)}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button
                                            onClick={() => handleEditClick(u)}
                                            className="p-2 text-[#8E8780] hover:text-[#ECE7E1] hover:bg-[#2A262E] rounded-lg transition-all cursor-pointer inline-flex items-center gap-2 text-xs font-bold uppercase"
                                        >
                                            <Edit2 className="w-4 h-4" /> Editar
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal de Edición */}
            {selectedUser && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
                    <div className="bg-[#141217] border border-[#2A262E] w-full max-w-md rounded-2xl p-6 shadow-2xl relative space-y-6">
                        <button
                            onClick={() => setSelectedUser(null)}
                            className="absolute top-4 right-4 text-[#8E8780] hover:text-white cursor-pointer"
                        >
                            <X className="w-5 h-5" />
                        </button>

                        <div>
                            <h3 className="text-lg font-bold font-display uppercase tracking-wider text-[#ECE7E1]">
                                Editar Usuario
                            </h3>
                            <p className="text-xs font-mono text-[#8E8780] mt-1">{selectedUser.email}</p>
                        </div>

                        <div className="space-y-4">
                            {/* Selector de Rol */}
                            <div className="space-y-1">
                                <label className="text-[10px] font-mono text-[#8E8780] uppercase">Rol Principal</label>
                                <select
                                    value={editRole}
                                    onChange={(e) => setEditRole(e.target.value)}
                                    className="w-full bg-[#0E0D0F] border border-[#2A262E] rounded-xl p-3 text-sm text-[#ECE7E1] focus:border-[#E5484D] outline-none cursor-pointer"
                                >
                                    <option value="Usuario">Usuario Estándar</option>
                                    <option value="Super Admin">Super Admin (Acceso Total)</option>
                                </select>
                            </div>

                            {/* Toggle Premium */}
                            <div className="flex items-center justify-between p-4 bg-[#0E0D0F] border border-[#2A262E] rounded-xl">
                                <div className="flex items-center gap-3">
                                    <Crown className={`w-5 h-5 ${editPremium ? 'text-amber-400' : 'text-[#8E8780]'}`} />
                                    <div>
                                        <span className="text-sm font-bold text-[#ECE7E1] block">Suscripción Pro</span>
                                        <span className="text-[10px] text-[#8E8780]">Acceso a APIs de IA</span>
                                    </div>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        className="sr-only peer"
                                        checked={editPremium}
                                        onChange={(e) => setEditPremium(e.target.checked)}
                                    />
                                    <div className="w-11 h-6 bg-[#2A262E] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
                                </label>
                            </div>
                        </div>

                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={() => setSelectedUser(null)}
                                className="flex-1 py-3 bg-[#1E1A24] hover:bg-[#2A2433] text-[#ECE7E1] text-xs font-bold uppercase tracking-wider rounded-xl transition-colors cursor-pointer"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={saving}
                                className="flex-1 py-3 bg-[#E5484D] hover:bg-[#B3261E] text-white text-xs font-bold uppercase tracking-wider rounded-xl transition-colors flex justify-center items-center gap-2 cursor-pointer disabled:opacity-50"
                            >
                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                {saving ? "Guardando" : "Guardar"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}