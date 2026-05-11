/**
 * useAudioClock — manages WebAudio playback and exposes the audio clock.
 *
 * Uses AudioContext.currentTime as the authoritative time source.
 * This never drifts against the audio buffer, unlike requestAnimationFrame timestamps.
 *
 * Returns:
 *   audioRef     — pass to <audio> element via ref
 *   currentTime  — seconds (updated each RAF)
 *   isPlaying
 *   play / pause / seek
 */

import { useCallback, useEffect, useRef, useState } from "react";

export interface AudioClockResult {
  currentTime: number;
  isPlaying: boolean;
  play: () => Promise<void>;
  pause: () => void;
  seek: (t: number) => void;
  loadUrl: (url: string) => Promise<void>;
}

export function useAudioClock(): AudioClockResult {
  const contextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);
  const bufferRef = useRef<AudioBuffer | null>(null);
  const startOffsetRef = useRef(0);   // AudioContext.currentTime when play() was called
  const seekOffsetRef = useRef(0);    // song position at last seek/play, seconds

  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const rafRef = useRef<number>(0);

  const getCtx = () => {
    if (!contextRef.current) {
      contextRef.current = new AudioContext();
    }
    return contextRef.current;
  };

  const tick = useCallback(() => {
    const ctx = contextRef.current;
    if (ctx && isPlaying) {
      const t = seekOffsetRef.current + (ctx.currentTime - startOffsetRef.current);
      setCurrentTime(t);
    }
    rafRef.current = requestAnimationFrame(tick);
  }, [isPlaying]);

  useEffect(() => {
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [tick]);

  const loadUrl = useCallback(async (url: string) => {
    const ctx = getCtx();
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    bufferRef.current = await ctx.decodeAudioData(arrayBuffer);
  }, []);

  const play = useCallback(async () => {
    if (!bufferRef.current) return;
    const ctx = getCtx();
    await ctx.resume();

    sourceRef.current?.stop();
    const source = ctx.createBufferSource();
    source.buffer = bufferRef.current;
    source.connect(ctx.destination);
    source.start(0, seekOffsetRef.current);
    source.onended = () => setIsPlaying(false);

    sourceRef.current = source;
    startOffsetRef.current = ctx.currentTime;
    setIsPlaying(true);
  }, []);

  const pause = useCallback(() => {
    const ctx = contextRef.current;
    if (!ctx) return;
    seekOffsetRef.current += ctx.currentTime - startOffsetRef.current;
    sourceRef.current?.stop();
    setIsPlaying(false);
  }, []);

  const seek = useCallback((t: number) => {
    seekOffsetRef.current = t;
    if (isPlaying) {
      void play();
    }
  }, [isPlaying, play]);

  return { currentTime, isPlaying, play, pause, seek, loadUrl };
}
