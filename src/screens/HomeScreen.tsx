import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import SearchBar from '../components/SearchBar';
import TrackCard from '../components/TrackCard';
import { searchTracks } from '../api/music';
import { usePlayer } from '../context/PlayerContext';
import { usePlayerStore } from '../store/playerStore';
import { useDownloadStore } from '../store/downloadStore';
import { useDownloader } from '../hooks/useDownloader';
import { theme, spacing, radius } from '../constants/theme';
import type { Track } from '../types';

const TABS = ['trend', 'myMusic'] as const;
type Tab = (typeof TABS)[number];

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const [query, setQuery] = useState('');
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [tab, setTab] = useState<Tab>('trend');
  const [error, setError] = useState('');

  const { playTrack } = usePlayer();
  const { currentTrack, isPlaying } = usePlayerStore();
  const { downloads } = useDownloadStore();
  const { download, isDownloaded, isDownloading, getProgress } = useDownloader();

  const myMusicList = Object.values(downloads).sort((a, b) => b.downloadedAt - a.downloadedAt);

  const loadTrending = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError('');
    try {
      const res = await searchTracks('');
      setTracks(res);
    } catch (e) {
      setError('Bağlantı hatası. Tekrar dene.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadTrending();
  }, []);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) { loadTrending(); return; }
    setLoading(true);
    setError('');
    setTab('trend');
    try {
      const res = await searchTracks(query);
      setTracks(res);
    } catch {
      setError('Arama başarısız oldu.');
    } finally {
      setLoading(false);
    }
  }, [query]);

  const handlePlay = useCallback(
    (track: Track) => {
      const list = tab === 'myMusic' ? myMusicList : tracks;
      playTrack(track, list);
    },
    [tracks, myMusicList, tab, playTrack]
  );

  const displayList: Track[] = tab === 'trend' ? tracks : myMusicList;

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.logo}>
          Flux<Text style={styles.logoAccent}>Music</Text>
        </Text>
      </View>

      {/* Search */}
      <View style={styles.searchWrap}>
        <SearchBar
          value={query}
          onChangeText={setQuery}
          onSubmit={handleSearch}
          loading={loading}
        />
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tabBtn, tab === 'trend' && styles.tabActive]}
          onPress={() => setTab('trend')}
        >
          <Ionicons name="flash" size={14} color={tab === 'trend' ? '#fff' : theme.muted} />
          <Text style={[styles.tabText, tab === 'trend' && styles.tabTextActive]}>Trendler</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabBtn, tab === 'myMusic' && styles.tabActive]}
          onPress={() => setTab('myMusic')}
        >
          <Ionicons
            name="cloud-download"
            size={14}
            color={tab === 'myMusic' ? '#fff' : theme.muted}
          />
          <Text style={[styles.tabText, tab === 'myMusic' && styles.tabTextActive]}>
            Müziklerim
          </Text>
          {myMusicList.length > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{myMusicList.length}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Content */}
      {loading && !refreshing ? (
        <View style={styles.center}>
          <ActivityIndicator color={theme.accent} size="large" />
          <Text style={styles.loadingText}>Evren taranıyor...</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Ionicons name="warning-outline" size={42} color={theme.muted} />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={() => loadTrending()}>
            <Text style={styles.retryText}>Tekrar Dene</Text>
          </TouchableOpacity>
        </View>
      ) : tab === 'myMusic' && myMusicList.length === 0 ? (
        <View style={styles.center}>
          <Ionicons name="musical-notes-outline" size={52} color={theme.muted} />
          <Text style={styles.emptyTitle}>Henüz müzik yok</Text>
          <Text style={styles.emptyDesc}>İndirdiğin müzikler burada görünür</Text>
        </View>
      ) : (
        <FlatList
          data={displayList}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefreshing(true); loadTrending(true); }}
              tintColor={theme.accent}
            />
          }
          renderItem={({ item }) => (
            <TrackCard
              track={item}
              isCurrentTrack={currentTrack?.id === item.id}
              isPlaying={isPlaying}
              isDownloaded={isDownloaded(item.id)}
              isDownloading={isDownloading(item.id)}
              downloadProgress={getProgress(item.id)}
              onPlay={handlePlay}
              onDownload={download}
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
    alignItems: 'center',
    paddingVertical: spacing.md,
  },
  logo: {
    fontSize: 26,
    fontWeight: '800',
    color: theme.text,
    letterSpacing: -0.5,
  },
  logoAccent: {
    color: theme.accent,
  },
  searchWrap: {
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.md,
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: spacing.xl,
    gap: spacing.md,
    marginBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.border,
    paddingBottom: spacing.md,
  },
  tabBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: radius.sm,
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: theme.accent,
  },
  tabText: {
    color: theme.muted,
    fontSize: 14,
    fontWeight: '700',
  },
  tabTextActive: {
    color: '#fff',
  },
  badge: {
    backgroundColor: theme.accent,
    borderRadius: 10,
    paddingHorizontal: 5,
    paddingVertical: 1,
    minWidth: 18,
    alignItems: 'center',
  },
  badgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
  list: {
    paddingHorizontal: spacing.xl,
    paddingBottom: 160,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    color: theme.muted,
    fontSize: 14,
    marginTop: 8,
  },
  errorText: {
    color: theme.muted,
    fontSize: 14,
    textAlign: 'center',
  },
  retryBtn: {
    backgroundColor: theme.accentDark,
    borderRadius: radius.md,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.sm,
    borderWidth: 1,
    borderColor: theme.accent,
  },
  retryText: {
    color: theme.accent,
    fontWeight: '700',
  },
  emptyTitle: {
    color: theme.text,
    fontSize: 18,
    fontWeight: '700',
  },
  emptyDesc: {
    color: theme.muted,
    fontSize: 13,
  },
});
