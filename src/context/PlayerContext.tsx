import React, {
  createContext,
  useContext,
  useRef,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import { Audio, type AVPlaybackStatus } from 'expo-av';
import { usePlayerStore } from '../store/playerStore';
import { streamUrl, API_SERVERS } from '../constants/config';
import type { Track } from '../types';

/* ─── Audio Mode: background playback ─── */
async function initAudio() {
  await Audio.setAudioModeAsync({
    staysActiveInBackground: true,
    shouldDuckAndroid: false,
    playThroughEarpieceAndroid: false,
    allowsRecordingIOS: false,
    playsInSilentModeIOS: true,
  });
}

/* ─── Context ─── */
interface PlayerContextType {
  playTrack: (track: Track, queue?: Track[]) => Promise<void>;
  togglePlayPause: () => Promise<void>;
  seek: (seconds: number) => Promise<void>;
  setVolume: (v: number) => Promise<void>;
  nextTrack: () => Promise<void>;
  prevTrack: () => Promise<void>;
  toggleRepeat: () => void;
  toggleShuffle: () => void;
}

const PlayerContext = createContext<PlayerContextType | null>(null);

export function PlayerProvider({ children }: { children: ReactNode }) {
  const soundRef = useRef<Audio.Sound | null>(null);
  const store = usePlayerStore();

  // Init audio mode once
  useEffect(() => { initAudio(); }, []);

  const onStatus = useCallback(
    (status: AVPlaybackStatus) => {
      if (!status.isLoaded) return;
      store.setIsPlaying(status.isPlaying);
      store.setPosition((status.positionMillis ?? 0) / 1000);
      store.setDuration((status.durationMillis ?? 0) / 1000);
      store.setIsLoading(false);

      if (status.didJustFinish) {
        handleEnd();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [store.repeatMode, store.currentIndex, store.queue, store.isShuffle]
  );

  const handleEnd = useCallback(() => {
    const { repeatMode, currentIndex, queue } = usePlayerStore.getState();
    if (repeatMode === 'one') {
      soundRef.current?.replayAsync();
    } else {
      const nextIdx = getNextIndex(currentIndex, queue.length, false);
      if (nextIdx !== -1) loadIndex(nextIdx);
    }
  }, []);

  function getNextIndex(current: number, total: number, prev: boolean): number {
    const { repeatMode, isShuffle } = usePlayerStore.getState();
    if (total === 0) return -1;
    if (isShuffle) return Math.floor(Math.random() * total);
    if (prev) return current > 0 ? current - 1 : repeatMode !== 'none' ? total - 1 : -1;
    const next = current + 1;
    if (next < total) return next;
    return repeatMode !== 'none' ? 0 : -1;
  }

  async function loadIndex(index: number) {
    const { queue } = usePlayerStore.getState();
    if (index < 0 || index >= queue.length) return;
    const track = queue[index];
    store.setCurrentIndex(index);
    await loadSound(track);
  }

  async function loadSound(track: Track & { localUri?: string }) {
    store.setIsLoading(true);
    store.setPosition(0);
    store.setDuration(0);
    store.setCurrentTrack(track);

    // Unload previous
    if (soundRef.current) {
      await soundRef.current.stopAsync().catch(() => {});
      await soundRef.current.unloadAsync().catch(() => {});
      soundRef.current = null;
    }

    const uri: string = (track as any).localUri ?? streamUrl(track.id, 0);

    try {
      const { sound } = await Audio.Sound.createAsync(
        { uri, headers: (track as any).localUri ? {} : { 'Referer': 'https://www.youtube.com/' } },
        { shouldPlay: true, progressUpdateIntervalMillis: 500, volume: store.volume },
        onStatus
      );
      soundRef.current = sound;
    } catch (e) {
      // Retry with second server
      if (!(track as any).localUri) {
        try {
          const uri2 = streamUrl(track.id, 1);
          const { sound } = await Audio.Sound.createAsync(
            { uri: uri2 },
            { shouldPlay: true, progressUpdateIntervalMillis: 500, volume: store.volume },
            onStatus
          );
          soundRef.current = sound;
        } catch {
          store.setIsLoading(false);
        }
      } else {
        store.setIsLoading(false);
      }
    }
  }

  /* ─── Public API ─── */

  const playTrack = useCallback(async (track: Track, queue?: Track[]) => {
    if (queue) {
      const idx = queue.findIndex((t) => t.id === track.id);
      store.setQueue(queue, idx >= 0 ? idx : 0);
    }
    await loadSound(track);
  }, []);

  const togglePlayPause = useCallback(async () => {
    if (!soundRef.current) return;
    const status = await soundRef.current.getStatusAsync();
    if (!status.isLoaded) return;
    if (status.isPlaying) {
      await soundRef.current.pauseAsync();
    } else {
      await soundRef.current.playAsync();
    }
  }, []);

  const seek = useCallback(async (seconds: number) => {
    await soundRef.current?.setPositionAsync(seconds * 1000);
  }, []);

  const setVolume = useCallback(async (v: number) => {
    store.setVolume(v);
    await soundRef.current?.setVolumeAsync(v);
  }, []);

  const nextTrack = useCallback(async () => {
    const { currentIndex, queue } = usePlayerStore.getState();
    const idx = getNextIndex(currentIndex, queue.length, false);
    if (idx !== -1) await loadIndex(idx);
  }, []);

  const prevTrack = useCallback(async () => {
    const { currentIndex, position, queue } = usePlayerStore.getState();
    // If >3s played, restart current
    if (position > 3) {
      await soundRef.current?.setPositionAsync(0);
      return;
    }
    const idx = getNextIndex(currentIndex, queue.length, true);
    if (idx !== -1) await loadIndex(idx);
  }, []);

  const toggleRepeat = useCallback(() => {
    const order: Array<typeof store.repeatMode> = ['none', 'all', 'one'];
    const cur = usePlayerStore.getState().repeatMode;
    const next = order[(order.indexOf(cur) + 1) % order.length];
    store.setRepeatMode(next);
  }, []);

  const toggleShuffle = useCallback(() => {
    store.setIsShuffle(!usePlayerStore.getState().isShuffle);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      soundRef.current?.unloadAsync().catch(() => {});
    };
  }, []);

  return (
    <PlayerContext.Provider
      value={{ playTrack, togglePlayPause, seek, setVolume, nextTrack, prevTrack, toggleRepeat, toggleShuffle }}
    >
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer(): PlayerContextType {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
            }
