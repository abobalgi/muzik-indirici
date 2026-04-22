export interface Track {
  id: string;
  title: string;
  thumbnail: string;
  duration: string; // "3:45"
  durationSec?: number;
  artist?: string;
}

export interface DownloadedTrack extends Track {
  localUri: string;        // local audio file URI
  thumbUri: string;        // local thumbnail URI
  mediaAssetId?: string;   // expo-media-library asset ID
  downloadedAt: number;    // timestamp
}

export type RepeatMode = 'none' | 'all' | 'one';
