import React, { useState, useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import Navbar from "./components/Navbar";
import StudioPage from "./pages/studio/StudioPage";
import LibraryPage from "./pages/LibraryPage";
import SettingsPage from "./pages/settings/SettingsPage";

const viewComponents = {
  studio: StudioPage,
  library: LibraryPage,
  settings: SettingsPage,
};

export default function App() {
  const [currentTab, setCurrentTab] = useState("studio");
  const prevTabRef = useRef("studio");

  const handleTabChange = (newTab) => {
    prevTabRef.current = currentTab;
    setCurrentTab(newTab);
  };

  const ActiveView = viewComponents[currentTab];

  return (
    <div
      className="min-h-screen flex flex-col overflow-x-hidden"
      style={{ backgroundColor: "#0E0D0F", color: "#ECE7E1" }}
    >
      <Navbar currentTab={currentTab} setCurrentTab={handleTabChange} />

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
            <ActiveView />
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}