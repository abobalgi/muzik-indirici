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
import { theme, radius, spacing } from '../constants/theme';
import type { Track } from '../types';

interface Props {
  track: Track;
  isPlaying?: boolean;
  isCurrentTrack?: boolean;
  isDownloaded?: boolean;
  isDownloading?: boolean;
  downloadProgress?: number;
  showDelete?: boolean;
  onPlay: (track: Track) => void;
  onDownload?: (track: Track) => void;
  onDelete?: (track: Track) => void;
}

function TrackCard({
  track,
  isPlaying,
  isCurrentTrack,
  isDownloaded,
  isDownloading,
  downloadProgress = 0,
  showDelete,
  onPlay,
  onDownload,
  onDelete,
}: Props) {
  return (
    <TouchableOpacity
      style={[styles.card, isCurrentTrack && styles.cardActive]}
      onPress={() => onPlay(track)}
      activeOpacity={0.75}
    >
      {/* Thumbnail */}
      <View style={styles.thumbWrap}>
        {track.thumbnail ? (
          <Image source={{ uri: track.thumbnail }} style={styles.thumb} />
        ) : (
          <View style={[styles.thumb, styles.thumbPlaceholder]}>
            <Ionicons name="musical-note" size={22} color={theme.muted} />
          </View>
        )}
        {/* Playing indicator overlay */}
        {isCurrentTrack && (
          <View style={styles.overlay}>
            {isPlaying ? (
              <View style={styles.vizRow}>
                {[0.6, 1, 0.7, 0.9].map((h, i) => (
                  <View key={i} style={[styles.vizBar, { opacity: h }]} />
                ))}
              </View>
            ) : (
              <Ionicons name="pause" size={20} color="#fff" />
            )}
          </View>
        )}
      </View>

      {/* Info */}
      <View style={styles.info}>
        <Text style={[styles.title, isCurrentTrack && styles.titleActive]} numberOfLines={2}>
          {track.title}
        </Text>
        {track.artist ? (
          <Text style={styles.sub} numberOfLines={1}>
            {track.artist}
          </Text>
        ) : null}
        <Text style={styles.dur}>{track.duration}</Text>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        {showDelete ? (
          <TouchableOpacity
            style={[styles.iconBtn, styles.btnDelete]}
            onPress={() => onDelete?.(track)}
            hitSlop={8}
          >
            <Ionicons name="trash-outline" size={16} color={theme.accent} />
          </TouchableOpacity>
        ) : (
          onDownload && (
            <TouchableOpacity
              style={[styles.iconBtn, isDownloaded ? styles.btnDone : styles.btnDownload]}
              onPress={() => !isDownloaded && !isDownloading && onDownload(track)}
              hitSlop={8}
              disabled={isDownloaded || isDownloading}
            >
              {isDownloading ? (
                <View style={styles.progressRing}>
                  <ActivityIndicator size="small" color={theme.accent} />
                  <Text style={styles.progressText}>
                    {Math.round(downloadProgress * 100)}%
                  </Text>
                </View>
              ) : isDownloaded ? (
                <Ionicons name="checkmark" size={16} color={theme.green} />
              ) : (
                <Ionicons name="arrow-down" size={16} color={theme.accent} />
              )}
            </TouchableOpacity>
          )
        )}

        <TouchableOpacity
          style={[styles.iconBtn, styles.btnPlay]}
          onPress={() => onPlay(track)}
          hitSlop={8}
        >
          <Ionicons
            name={isCurrentTrack && isPlaying ? 'pause' : 'play'}
            size={15}
            color={theme.green}
          />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
}

export default memo(TrackCard);

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: theme.border,
    padding: spacing.sm,
    gap: spacing.md,
  },
  cardActive: {
    borderColor: theme.accent,
    backgroundColor: 'rgba(244,63,94,0.06)',
  },
  thumbWrap: {
    width: 60,
    height: 60,
    borderRadius: radius.md,
    overflow: 'hidden',
    flexShrink: 0,
    position: 'relative',
  },
  thumb: {
    width: 60,
    height: 60,
  },
  thumbPlaceholder: {
    backgroundColor: theme.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  vizRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 2,
  },
  vizBar: {
    width: 3,
    height: 16,
    backgroundColor: theme.accent,
    borderRadius: 2,
  },
  info: {
    flex: 1,
    minWidth: 0,
    paddingRight: 4,
  },
  title: {
    fontSize: 13.5,
    fontWeight: '600',
    color: theme.text,
    marginBottom: 3,
  },
  titleActive: {
    color: theme.accent,
  },
  sub: {
    fontSize: 11.5,
    color: theme.muted,
    marginBottom: 2,
  },
  dur: {
    fontSize: 11,
    color: theme.mutedLight,
  },
  actions: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
    flexShrink: 0,
  },
  iconBtn: {
    width: 34,
    height: 34,
    borderRadius: radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnPlay: {
    backgroundColor: theme.greenDark,
  },
  btnDownload: {
    backgroundColor: theme.accentDark,
  },
  btnDone: {
    backgroundColor: theme.greenDark,
  },
  btnDelete: {
    backgroundColor: theme.accentDark,
  },
  progressRing: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressText: {
    fontSize: 7,
    color: theme.accent,
    position: 'absolute',
  },
});
        
