import React, { useState, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import PipelineRail from "../../components/studio/PipelineRail";
import PreviewPanel from "../../components/studio/PreviewPanel";
import FloatingTerminal from "../../components/FloatingTerminal";
import SourceStep from "./SourceStep";
import StoriesStep from "./StoriesStep";
import EditStep from "./EditStep";
import VoiceStep from "./VoiceStep";
import SubtitlesStep from "./SubtitlesStep";
import BackgroundStep from "./BackgroundStep";
import RenderStep from "./RenderStep";
import { createProject, getProject, runProjectStep, subscribeJobEvents, cancelJob } from "../../api/client";

const stepComponents = {
  1: SourceStep,
  2: StoriesStep,
  3: EditStep,
  4: VoiceStep,
  5: SubtitlesStep,
  6: BackgroundStep,
  7: RenderStep,
};

export default function StudioPage() {
  const [project, setProject] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [activeJobId, setActiveJobId] = useState(null);
  const [events, setEvents] = useState([]);
  const prevStepRef = useRef(1);

  useEffect(() => {
    // Inicializar o cargar proyecto por defecto
    createProject({ subreddit: "nosleep" })
      .then((p) => setProject(p))
      .catch(console.error);
  }, []);

  // Track direction for slide animation
  const handleStepChange = (newStep) => {
    prevStepRef.current = currentStep;
    setCurrentStep(newStep);
  };

  const slideDirection = currentStep > prevStepRef.current ? 1 : -1;

  // Helper for immediate React state update
  const handleUpdateProjectState = (partialData) => {
    setProject((prev) => (prev ? { ...prev, ...partialData } : prev));
  };

  const handleRunStep = async (stepName, args = {}) => {
    if (!project) return;
    setLoading(true);
    setEvents([]);

    try {
      const jobRes = await runProjectStep(project.id, stepName, args);
      setActiveJobId(jobRes.job_id);

      subscribeJobEvents(
        jobRes.job_id,
        (evt) => {
          setEvents((prev) => [...prev, evt]);
        },
        (err) => {
          console.error("Job SSE error", err);
          setLoading(false);
        },
        async () => {
          // Job complete: refresh project state from backend
          const updated = await getProject(project.id);
          setProject(updated);
          setLoading(false);

          if (stepName === "search_stories") {
            handleStepChange(2);
          } else if (stepName === "accept_stories" && currentStep === 2) {
            handleStepChange(3);
          }
        }
      );
    } catch (e) {
      alert(`Error al ejecutar paso: ${e.message}`);
      setLoading(false);
    }
  };

  const handleCancelActiveJob = async () => {
    if (activeJobId) {
      try {
        await cancelJob(activeJobId);
        setLoading(false);
        alert("Proceso cancelado correctamente");
      } catch (err) {
        console.error("Error al cancelar job:", err);
      }
    }
  };

  if (!project) {
    return (
      <div className="p-12 text-center text-[#8E8780] font-mono text-xs">
        Iniciando estudio de producción...
      </div>
    );
  }

  const StepComponent = stepComponents[currentStep];
  const stepProps = {
    project,
    onRunStep: handleRunStep,
    loading,
    onUpdateProject: handleUpdateProjectState,
    ...(currentStep === 7 ? { events, onCancelJob: handleCancelActiveJob } : {}),
  };

  return (
    <div
      className="flex h-[calc(100vh-4rem)] overflow-hidden relative"
      style={{ backgroundColor: "#0E0D0F" }}
    >
      {/* 1. Left Pipeline Rail */}
      <PipelineRail
        currentStep={currentStep}
        setCurrentStep={handleStepChange}
        project={project}
        loading={loading}
      />

      {/* 2. Center Workspace with Animated Step Transitions */}
      <main className="flex-1 overflow-hidden relative" style={{ backgroundColor: "#0E0D0F" }}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: slideDirection * 32 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: slideDirection * -32 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="h-full overflow-y-auto p-6"
            style={{ backgroundColor: "#0E0D0F" }}
          >
            <StepComponent {...stepProps} />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* 3. Right Preview Panel */}
      <PreviewPanel project={project} />

      {/* 4. OS Floating Log Window */}
      <FloatingTerminal
        events={events}
        isRunning={loading}
      />
    </div>
  );
}
