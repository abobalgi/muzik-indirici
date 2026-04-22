import { fetchSmart } from '../constants/config';
import type { Track } from '../types';

function parseDuration(raw: any): string {
  if (typeof raw === 'string') return raw;
  if (typeof raw === 'number') {
    const m = Math.floor(raw / 60);
    const s = Math.floor(raw % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }
  return '0:00';
}

export async function searchTracks(query: string): Promise<Track[]> {
  const q = query.trim() ? `?q=${encodeURIComponent(query.trim())}` : '';
  const res = await fetchSmart(`/search${q}`);
  const data: any[] = await res.json();
  return data.map((item) => ({
    id: item.id ?? '',
    title: item.title ?? 'Bilinmiyor',
    thumbnail: item.thumbnail ?? '',
    duration: parseDuration(item.duration),
    durationSec: typeof item.duration === 'number' ? item.duration : undefined,
    artist: item.author ?? item.artist ?? '',
  }));
}

export async function fetchLyrics(query: string): Promise<{ plain: string; synced: string | null } | null> {
  try {
    const res = await fetchSmart(`/lyrics?q=${encodeURIComponent(query)}`);
    if (!res.ok) return null;
    const data = await res.json();
    return { plain: data.lyrics ?? '', synced: data.synced ?? null };
  } catch {
    return null;
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetchSmart('/health');
    return res.ok;
  } catch {
    return false;
  }
}
  
