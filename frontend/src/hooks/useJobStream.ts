/**
 * useJobStream — subscribes to the SSE progress stream for a pipeline job.
 *
 * Returns the latest JobEvent (or null while waiting for first event).
 * Falls back to polling /status/{jobId} every 2s in environments that
 * don't support EventSource (rare, but covers some corp proxies).
 */

import { useEffect, useState } from "react";

export interface JobEvent {
  job_id: string;
  status: "queued" | "processing" | "done" | "error";
  step: string;
  pct: number;
  msg: string;
  error: string | null;
}

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function useJobStream(jobId: string | null): JobEvent | null {
  const [event, setEvent] = useState<JobEvent | null>(null);

  useEffect(() => {
    if (!jobId) return;

    if (typeof EventSource !== "undefined") {
      // Primary path: SSE
      const es = new EventSource(`${API}/stream/${jobId}`);
      es.onmessage = (e) => {
        const data: JobEvent = JSON.parse(e.data);
        setEvent(data);
        if (data.status === "done" || data.status === "error") {
          es.close();
        }
      };
      es.onerror = () => es.close();
      return () => es.close();
    } else {
      // Fallback: polling
      let active = true;
      const poll = async () => {
        while (active) {
          const res = await fetch(`${API}/status/${jobId}`);
          const data: JobEvent = await res.json();
          setEvent(data);
          if (data.status === "done" || data.status === "error") break;
          await new Promise((r) => setTimeout(r, 2000));
        }
      };
      void poll();
      return () => { active = false; };
    }
  }, [jobId]);

  return event;
}

export function uploadAudio(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  return fetch(`${API}/process`, { method: "POST", body: form })
    .then((r) => r.json())
    .then((j) => j.job_id as string);
}

export function hvizUrl(jobId: string): string {
  return `${API}/hviz/${jobId}`;
}

export function audioUrl(jobId: string): string {
  return `${API}/audio/${jobId}`;
}
