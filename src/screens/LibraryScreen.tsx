import React, { useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  Alert,
  TouchableOpacity,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import TrackCard from '../components/TrackCard';
import { usePlayer } from '../context/PlayerContext';
import { usePlayerStore } from '../store/playerStore';
import { useDownloadStore } from '../store/downloadStore';
import { useDownloader } from '../hooks/useDownloader';
import { theme, spacing } from '../constants/theme';
import type { Track } from '../types';

export default function LibraryScreen() {
  const insets = useSafeAreaInsets();
  const { playTrack } = usePlayer();
  const { currentTrack, isPlaying } = usePlayerStore();
  const { downloads } = useDownloadStore();
  const { deleteDownload } = useDownloader();

  const list = Object.values(downloads).sort((a, b) => b.downloadedAt - a.downloadedAt);

  const handlePlay = useCallback(
    (track: Track) => {
      playTrack(track, list);
    },
    [list, playTrack]
  );

  const handleDelete = useCallback((track: Track) => {
    Alert.alert(
      'Müziği Sil',
      `"${track.title}" silinsin mi?`,
      [
        { text: 'İptal', style: 'cancel' },
        {
          text: 'Sil',
          style: 'destructive',
          onPress: () => deleteDownload(track.id),
        },
      ]
    );
  }, [deleteDownload]);

  const totalSize = list.length;

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Kütüphane</Text>
        {totalSize > 0 && (
          <Text style={styles.subtitle}>{totalSize} müzik indirildi</Text>
        )}
      </View>

      {list.length === 0 ? (
        <View style={styles.empty}>
          <Ionicons name="library-outline" size={64} color={theme.muted} />
          <Text style={styles.emptyTitle}>Kütüphane boş</Text>
          <Text style={styles.emptyDesc}>
            Keşfet sekmesinden müzik indirince burada belirir
          </Text>
        </View>
      ) : (
        <FlatList
          data={list}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => (
            <TrackCard
              track={item}
              isCurrentTrack={currentTrack?.id === item.id}
              isPlaying={isPlaying}
              isDownloaded
              showDelete
              onPlay={handlePlay}
              onDelete={handleDelete}
            />
          )}
          ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: theme.bg,
  },
  header: {
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.border,
  },
  title: {
    color: theme.text,
    fontSize: 24,
    fontWeight: '800',
  },
  subtitle: {
    color: theme.muted,
    fontSize: 13,
    marginTop: 4,
  },
  list: {
    padding: spacing.xl,
    paddingBottom: 160,
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: spacing.xl,
  },
  emptyTitle: {
    color: theme.text,
    fontSize: 20,
    fontWeight: '700',
  },
  emptyDesc: {
    color: theme.muted,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 21,
  },
});
      
