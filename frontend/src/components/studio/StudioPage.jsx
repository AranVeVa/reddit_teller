const GenerationAction = ({ currentUser }) => {
    // Validamos si es Super Admin o tiene membresía Premium
    const canGenerate = currentUser?.role === 'Super Admin' || currentUser?.isPremium;

    return (
        <div className="flex flex-col items-center">
            {canGenerate ? (
                <button
                    onClick={handleGenerateVideo}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded shadow-md transition-colors"
                >
                    Generar Video con IA
                </button>
            ) : (
                <div className="text-center p-4 bg-gray-100 rounded border border-gray-300">
                    <p className="text-gray-600 mb-2">Esta función es exclusiva para usuarios Premium o Administradores.</p>
                    <button className="bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-2 px-4 rounded transition-colors">
                        Mejorar a Premium
                    </button>
                </div>
            )}
        </div>
    );
};