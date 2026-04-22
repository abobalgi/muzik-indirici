import React, { memo } from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { usePlayerStore } from '../store/playerStore';
import { usePlayer } from '../context/PlayerContext';
import { theme, radius, spacing } from '../constants/theme';

interface Props {
  bottomTabsHeight: number;
}

function MiniPlayer({ bottomTabsHeight }: Props) {
  const { currentTrack, isPlaying, isLoading } = usePlayerStore();
  const { togglePlayPause, nextTrack } = usePlayer();
  const { openPlayer } = usePlayerStore();
  const insets = useSafeAreaInsets();

  if (!currentTrack) return null;

  return (
    <View style={[styles.wrap, { bottom: bottomTabsHeight }]}>
      <TouchableOpacity style={styles.inner} onPress={openPlayer} activeOpacity={0.9}>
        {/* Thumbnail */}
        {currentTrack.thumbnail ? (
          <Image source={{ uri: currentTrack.thumbnail }} style={styles.thumb} />
        ) : (
          <View style={[styles.thumb, styles.thumbPlaceholder]}>
            <Ionicons name="musical-note" size={18} color={theme.muted} />
          </View>
        )}

        {/* Meta */}
        <View style={styles.meta}>
          <Text style={styles.title} numberOfLines={1}>
            {currentTrack.title}
          </Text>
          {currentTrack.artist ? (
            <Text style={styles.artist} numberOfLines={1}>
              {currentTrack.artist}
            </Text>
          ) : null}
        </View>

        {/* Controls */}
        <View style={styles.controls}>
          <TouchableOpacity
            onPress={(e) => { e.stopPropagation(); togglePlayPause(); }}
            style={styles.ctrlBtn}
            hitSlop={8}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color={theme.accent} />
            ) : (
              <Ionicons
                name={isPlaying ? 'pause' : 'play'}
                size={26}
                color={theme.accent}
              />
            )}
          </TouchableOpacity>
          <TouchableOpacity
            onPress={(e) => { e.stopPropagation(); nextTrack(); }}
            style={styles.ctrlBtn}
            hitSlop={8}
          >
            <Ionicons name="play-skip-forward" size={20} color={theme.text} />
          </TouchableOpacity>
        </View>
      </TouchableOpacity>

      {/* Viz bars */}
      {isPlaying && (
        <View style={styles.viz} pointerEvents="none">
          {[1, 0.5, 0.8, 0.3, 0.9].map((o, i) => (
            <View key={i} style={[styles.vizBar, { opacity: o }]} />
          ))}
        </View>
      )}
    </View>
  );
}

export default memo(MiniPlayer);

const styles = StyleSheet.create({
  wrap: {
    position: 'absolute',
    left: 0,
    right: 0,
    backgroundColor: 'rgba(9,9,11,0.97)',
    borderTopWidth: 1,
    borderTopColor: theme.border,
    overflow: 'hidden',
  },
  inner: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.sm,
    gap: spacing.md,
  },
  thumb: {
    width: 44,
    height: 44,
    borderRadius: radius.sm,
    flexShrink: 0,
  },
  thumbPlaceholder: {
    backgroundColor: theme.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  meta: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    color: theme.text,
    fontSize: 14,
    fontWeight: '700',
  },
  artist: {
    color: theme.accent,
    fontSize: 12,
    marginTop: 2,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    flexShrink: 0,
  },
  ctrlBtn: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  viz: {
    position: 'absolute',
    left: 0,
    bottom: 0,
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 3,
    paddingLeft: 6,
    height: 3,
  },
  vizBar: {
    width: 3,
    height: 3,
    backgroundColor: theme.accent,
    borderRadius: 2,
  },
});
