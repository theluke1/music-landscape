import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer, Bloom, ChromaticAberration, DepthOfField } from "@react-three/postprocessing";
import { useMusicalStore } from "./store";
import { useAudioClock } from "./hooks/useAudioClock";
import { useFeatureFrame } from "./hooks/useFeatureFrame";
import { PitchHelix } from "./scene/PitchHelix";
import { BassOrbShell } from "./scene/BassOrbShell";
import { PercussionCrystals } from "./scene/PercussionCrystals";
import { ChladniFloor } from "./scene/ChladniFloor";

function SceneContent() {
  const { currentTime } = useAudioClock();
  useFeatureFrame(currentTime);

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

export default function App() {
  const loadHviz = useMusicalStore((s) => s.loadHviz);

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const text = await file.text();
    loadHviz(JSON.parse(text));
  };

  return (
    <div
      style={{ width: "100vw", height: "100vh", background: "#000" }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <Canvas
        camera={{ position: [0, 4, 10], fov: 60 }}
        gl={{ antialias: false, powerPreference: "high-performance" }}
      >
        <SceneContent />
        <OrbitControls enablePan={false} minDistance={4} maxDistance={30} />
      </Canvas>
    </div>
  );
}
