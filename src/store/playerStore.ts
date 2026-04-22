import { create } from 'zustand';
import type { Track, RepeatMode } from '../types';

interface PlayerState {
  currentTrack: Track | null;
  queue: Track[];
  currentIndex: number;
  isPlaying: boolean;
  isLoading: boolean;
  position: number;  // seconds
  duration: number;  // seconds
  volume: number;    // 0–1
  repeatMode: RepeatMode;
  isShuffle: boolean;
  isPlayerOpen: boolean;

  // Actions
  setCurrentTrack: (track: Track | null) => void;
  setQueue: (queue: Track[], index?: number) => void;
  setCurrentIndex: (index: number) => void;
  setIsPlaying: (v: boolean) => void;
  setIsLoading: (v: boolean) => void;
  setPosition: (v: number) => void;
  setDuration: (v: number) => void;
  setVolume: (v: number) => void;
  setRepeatMode: (mode: RepeatMode) => void;
  setIsShuffle: (v: boolean) => void;
  togglePlayerOpen: () => void;
  openPlayer: () => void;
  closePlayer: () => void;
}

export const usePlayerStore = create<PlayerState>((set) => ({
  currentTrack: null,
  queue: [],
  currentIndex: -1,
  isPlaying: false,
  isLoading: false,
  position: 0,
  duration: 0,
  volume: 1,
  repeatMode: 'none',
  isShuffle: false,
  isPlayerOpen: false,

  setCurrentTrack: (track) => set({ currentTrack: track }),
  setQueue: (queue, index = 0) => set({ queue, currentIndex: index }),
  setCurrentIndex: (index) => set({ currentIndex: index }),
  setIsPlaying: (v) => set({ isPlaying: v }),
  setIsLoading: (v) => set({ isLoading: v }),
  setPosition: (v) => set({ position: v }),
  setDuration: (v) => set({ duration: v }),
  setVolume: (v) => set({ volume: v }),
  setRepeatMode: (mode) => set({ repeatMode: mode }),
  setIsShuffle: (v) => set({ isShuffle: v }),
  togglePlayerOpen: () => set((s) => ({ isPlayerOpen: !s.isPlayerOpen })),
  openPlayer: () => set({ isPlayerOpen: true }),
  closePlayer: () => set({ isPlayerOpen: false }),
}));
