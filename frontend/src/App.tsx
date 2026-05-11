import { useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import {
  EffectComposer,
  Bloom,
  ChromaticAberration,
  DepthOfField,
} from "@react-three/postprocessing";

import { useMusicalStore } from "./store";
import { useAudioClock } from "./hooks/useAudioClock";
import { useFeatureFrame } from "./hooks/useFeatureFrame";
import { hvizUrl, audioUrl } from "./hooks/useJobStream";
import { UploadPanel } from "./components/UploadPanel";
import { PitchHelix } from "./scene/PitchHelix";
import { BassOrbShell } from "./scene/BassOrbShell";
import { PercussionCrystals } from "./scene/PercussionCrystals";
import { ChladniFloor } from "./scene/ChladniFloor";

// ---------------------------------------------------------------------------
// Scene — only mounts after a job is ready
// ---------------------------------------------------------------------------
function Scene({ jobId }: { jobId: string }) {
  const loadHviz = useMusicalStore((s) => s.loadHviz);
  const { currentTime, loadUrl, play } = useAudioClock();
  useFeatureFrame(currentTime);

  // Load features + audio once on mount
  useEffect(() => {
    async function init() {
      const [hvizRes] = await Promise.all([
        fetch(hvizUrl(jobId)).then((r) => r.json()),
        loadUrl(audioUrl(jobId)),
      ]);
      loadHviz(hvizRes);
      await play();
    }
    void init();
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <PitchHelix />
      <BassOrbShell />
      <PercussionCrystals />
      <ChladniFloor />

      <EffectComposer>
        <Bloom luminanceThreshold={0.6} luminanceSmoothing={0.4} intensity={0.8} />
        <ChromaticAberration offset={[0.0005, 0.0005]} />
        <DepthOfField focusDistance={0} focalLength={0.02} bokehScale={2} />
      </EffectComposer>
    </>
  );
}

// ---------------------------------------------------------------------------
// App root — shows UploadPanel until a job completes, then the scene
// ---------------------------------------------------------------------------
export default function App() {
  const jobId = useMusicalStore((s) => s.jobId);
  const setJobId = useMusicalStore((s) => s.setJobId);

  if (!jobId) {
    return <UploadPanel onReady={setJobId} />;
  }

  return (
    <Canvas
      style={{ width: "100vw", height: "100vh", background: "#000" }}
      camera={{ position: [0, 4, 10], fov: 60 }}
      gl={{ antialias: false, powerPreference: "high-performance" }}
    >
      <Scene jobId={jobId} />
      <OrbitControls enablePan={false} minDistance={4} maxDistance={30} />
    </Canvas>
  );
}
