import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import AuthModal from './components/AuthModal';
import Footer from './components/Footer';
import Home from './pages/Home';
import CreateVideo from './pages/CreateVideo';
import VideoResult from './pages/VideoResult';

export default function App() {
  const [currentView, setCurrentView] = useState('home');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [generatedVideo, setGeneratedVideo] = useState(null);
  const [authModal, setAuthModal] = useState({ isOpen: false, mode: 'login' });

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const handleOpenAuth = (mode) => {
    setAuthModal({ isOpen: true, mode });
  };

  return (
    <div className={`min-h-screen flex flex-col font-sans theme-transition ${isDarkMode ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'
      }`}>

      <Navbar
        currentView={currentView}
        setCurrentView={setCurrentView}
        isDarkMode={isDarkMode}
        setIsDarkMode={setIsDarkMode}
        onOpenAuth={handleOpenAuth}
      />

      <main className="flex-1">
        {currentView === 'home' && (
          <Home onNavigateCreate={() => setCurrentView('create')} />
        )}

        {currentView === 'create' && (
          <CreateVideo onGenerated={(data) => { setGeneratedVideo(data); setCurrentView('result'); }} />
        )}

        {currentView === 'result' && (
          <VideoResult resultData={generatedVideo} onReset={() => setCurrentView('create')} />
        )}
      </main>

      <AuthModal
        isOpen={authModal.isOpen}
        initialMode={authModal.mode}
        onClose={() => setAuthModal({ ...authModal, isOpen: false })}
      />

      <Footer />
    </div>
  );
}