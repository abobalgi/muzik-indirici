import { useCallback } from 'react';
import * as FileSystem from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';
import { Alert } from 'react-native';
import { useDownloadStore } from '../store/downloadStore';
import { downloadUrl } from '../constants/config';
import type { Track, DownloadedTrack } from '../types';

export function useDownloader() {
  const store = useDownloadStore();

  const isDownloaded = useCallback(
    (videoId: string) => !!store.downloads[videoId],
    [store.downloads]
  );

  const isDownloading = useCallback(
    (videoId: string) => store.downloading[videoId] !== undefined,
    [store.downloading]
  );

  const getProgress = useCallback(
    (videoId: string) => store.downloading[videoId] ?? 0,
    [store.downloading]
  );

  const download = useCallback(
    async (track: Track): Promise<boolean> => {
      if (store.downloads[track.id] || store.downloading[track.id] !== undefined) return false;

      // Check permissions
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('İzin Gerekli', 'Müzik kaydetmek için depolama izni gereklidir.');
        return false;
      }

      store.setProgress(track.id, 0.01);

      const audioDir = FileSystem.documentDirectory + 'flux_music/';
      await FileSystem.makeDirectoryAsync(audioDir, { intermediates: true });

      const audioPath = audioDir + `${track.id}.m4a`;
      const thumbPath = audioDir + `${track.id}_thumb.jpg`;

      try {
        // 1) Download thumbnail first (small, fast)
        let localThumb = '';
        if (track.thumbnail) {
          try {
            await FileSystem.downloadAsync(track.thumbnail, thumbPath);
            localThumb = thumbPath;
          } catch {}
        }

        store.setProgress(track.id, 0.05);

        // 2) Download audio with progress tracking
        const dlResumable = FileSystem.createDownloadResumable(
          downloadUrl(track.id, 0),
          audioPath,
          {},
          ({ totalBytesWritten, totalBytesExpectedToWrite }) => {
            if (totalBytesExpectedToWrite > 0) {
              const pct = 0.05 + (totalBytesWritten / totalBytesExpectedToWrite) * 0.85;
              store.setProgress(track.id, Math.min(pct, 0.9));
            }
          }
        );

        const result = await dlResumable.downloadAsync();
        if (!result?.uri) throw new Error('İndirme başarısız');

        store.setProgress(track.id, 0.92);

        // 3) Save to Media Library (visible to system music players)
        const asset = await MediaLibrary.createAssetAsync(result.uri);
        let album = await MediaLibrary.getAlbumAsync('Flux Music');
        if (album) {
          await MediaLibrary.addAssetsToAlbumAsync([asset], album, false);
        } else {
          await MediaLibrary.createAlbumAsync('Flux Music', asset, false);
        }

        store.setProgress(track.id, 1);

        // 4) Persist metadata
        const downloaded: DownloadedTrack = {
          ...track,
          localUri: result.uri,
          thumbUri: localThumb,
          mediaAssetId: asset.id,
          downloadedAt: Date.now(),
        };
        await store.addDownload(downloaded);
        store.clearProgress(track.id);
        return true;
      } catch (e) {
        store.clearProgress(track.id);
        // Cleanup partial files
        await FileSystem.deleteAsync(audioPath, { idempotent: true });
        Alert.alert('İndirme Hatası', 'Müzik indirilemedi. İnternet bağlantını kontrol et.');
        return false;
      }
    },
    [store]
  );

  const deleteDownload = useCallback(
    async (videoId: string) => {
      const track = store.downloads[videoId];
      if (!track) return;

      // Remove files
      await FileSystem.deleteAsync(track.localUri, { idempotent: true });
      if (track.thumbUri) await FileSystem.deleteAsync(track.thumbUri, { idempotent: true });

      // Remove from media library
      if (track.mediaAssetId) {
        try {
          await MediaLibrary.deleteAssetsAsync([track.mediaAssetId]);
        } catch {}
      }

      await store.removeDownload(videoId);
    },
    [store]
  );

  return { download, deleteDownload, isDownloaded, isDownloading, getProgress };
          }
            
