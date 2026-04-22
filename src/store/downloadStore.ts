import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { DownloadedTrack } from '../types';

const STORAGE_KEY = 'flux_downloads_v2';

interface DownloadStore {
  downloads: Record<string, DownloadedTrack>;
  downloading: Record<string, number>; // videoId -> 0–1

  // Actions
  loadFromStorage: () => Promise<void>;
  addDownload: (track: DownloadedTrack) => Promise<void>;
  removeDownload: (videoId: string) => Promise<void>;
  setProgress: (videoId: string, progress: number) => void;
  clearProgress: (videoId: string) => void;
}

export const useDownloadStore = create<DownloadStore>((set, get) => ({
  downloads: {},
  downloading: {},

  loadFromStorage: async () => {
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      if (raw) set({ downloads: JSON.parse(raw) });
    } catch {}
  },

  addDownload: async (track) => {
    const updated = { ...get().downloads, [track.id]: track };
    set({ downloads: updated });
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch {}
  },

  removeDownload: async (videoId) => {
    const updated = { ...get().downloads };
    delete updated[videoId];
    set({ downloads: updated });
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch {}
  },

  setProgress: (videoId, progress) =>
    set((s) => ({ downloading: { ...s.downloading, [videoId]: progress } })),

  clearProgress: (videoId) =>
    set((s) => {
      const downloading = { ...s.downloading };
      delete downloading[videoId];
      return { downloading };
    }),
}));
