/**
 * UploadPanel — the pre-scene UI.
 *
 * States:
 *   idle       → drag-and-drop zone for an audio file
 *   uploading  → file is being POSTed to /process
 *   processing → SSE progress bar (step name + %)
 *   error      → error message + retry button
 *
 * On completion, calls onReady(jobId) so the parent can load
 * the .hviz and audio URLs and switch to the scene.
 */

import { useCallback, useRef, useState } from "react";
import { uploadAudio, useJobStream } from "../hooks/useJobStream";

interface Props {
  onReady: (jobId: string) => void;
}

const STEP_LABELS: Record<string, string> = {
  queued:     "Queued",
  separate:   "Separating stems (Demucs)…",
  pitch:      "Tracking melody + bass (CREPE)…",
  chroma:     "Extracting chroma + chords…",
  drums:      "Extracting drum features…",
  structure:  "Segmenting structure…",
  stft:       "Computing spectrogram…",
  perceptual: "Running perceptual model…",
  assemble:   "Assembling .hviz…",
};

export function UploadPanel({ onReady }: Props) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const event = useJobStream(jobId);

  // Trigger onReady once when done
  const readyFired = useRef(false);
  if (event?.status === "done" && jobId && !readyFired.current) {
    readyFired.current = true;
    onReady(jobId);
  }

  const submit = useCallback(async (file: File) => {
    setUploading(true);
    try {
      const id = await uploadAudio(file);
      setJobId(id);
    } finally {
      setUploading(false);
    }
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) void submit(file);
  }, [submit]);

  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void submit(file);
  }, [submit]);

  const isProcessing = uploading || (event && event.status !== "done" && event.status !== "error");
  const pct = event?.pct ?? 0;
  const stepLabel = event ? (STEP_LABELS[event.step] ?? event.msg) : uploading ? "Uploading…" : "";

  return (
    <div style={styles.root}>
      {!isProcessing && event?.status !== "error" && (
        <div
          style={{ ...styles.dropzone, ...(dragOver ? styles.dropzoneActive : {}) }}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept="audio/*"
            style={{ display: "none" }}
            onChange={onFileChange}
          />
          <span style={styles.dropIcon}>♩</span>
          <span style={styles.dropText}>Drop an audio file to begin</span>
          <span style={styles.dropSub}>mp3 · wav · flac · ogg</span>
        </div>
      )}

      {isProcessing && (
        <div style={styles.progress}>
          <span style={styles.stepLabel}>{stepLabel}</span>
          <div style={styles.barTrack}>
            <div style={{ ...styles.barFill, width: `${pct}%` }} />
          </div>
          <span style={styles.pctLabel}>{pct}%</span>
        </div>
      )}

      {event?.status === "error" && (
        <div style={styles.error}>
          <span>Processing failed: {event.error}</span>
          <button style={styles.retryBtn} onClick={() => { setJobId(null); readyFired.current = false; }}>
            Retry
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inline styles — no CSS file needed; this component lives once
// ---------------------------------------------------------------------------
const styles: Record<string, React.CSSProperties> = {
  root: {
    position: "fixed",
    inset: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#000",
    fontFamily: "monospace",
  },
  dropzone: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 12,
    border: "1px solid #333",
    borderRadius: 4,
    padding: "48px 64px",
    cursor: "pointer",
    transition: "border-color 0.15s",
    userSelect: "none",
  },
  dropzoneActive: {
    borderColor: "#888",
  },
  dropIcon: {
    fontSize: 48,
    color: "#555",
    lineHeight: 1,
  },
  dropText: {
    color: "#ccc",
    fontSize: 15,
    letterSpacing: "0.04em",
  },
  dropSub: {
    color: "#444",
    fontSize: 11,
    letterSpacing: "0.08em",
  },
  progress: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 16,
    width: 360,
  },
  stepLabel: {
    color: "#888",
    fontSize: 12,
    letterSpacing: "0.06em",
    textAlign: "center",
  },
  barTrack: {
    width: "100%",
    height: 2,
    background: "#1a1a1a",
    borderRadius: 1,
    overflow: "hidden",
  },
  barFill: {
    height: "100%",
    background: "#ccc",
    transition: "width 0.4s ease",
    borderRadius: 1,
  },
  pctLabel: {
    color: "#444",
    fontSize: 11,
  },
  error: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 16,
    color: "#c44",
    fontSize: 13,
    textAlign: "center",
    maxWidth: 360,
  },
  retryBtn: {
    background: "none",
    border: "1px solid #333",
    color: "#888",
    padding: "6px 20px",
    borderRadius: 3,
    cursor: "pointer",
    fontFamily: "monospace",
    fontSize: 12,
  },
};
