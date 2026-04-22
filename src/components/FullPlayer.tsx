import React, { useCallback, useRef, useEffect, memo } from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  Animated,
  PanResponder,
  Dimensions,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import Slider from '@react-native-community/slider';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { usePlayerStore } from '../store/playerStore';
import { usePlayer } from '../context/PlayerContext';
import { theme, radius, spacing } from '../constants/theme';

const { height: SCREEN_H } = Dimensions.get('window');

function fmt(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

function FullPlayer() {
  const store = usePlayerStore();
  const { togglePlayPause, seek, setVolume, nextTrack, prevTrack, toggleRepeat, toggleShuffle } =
    usePlayer();
  const insets = useSafeAreaInsets();
  const slideY = useRef(new Animated.Value(SCREEN_H)).current;
  const vinylSpin = useRef(new Animated.Value(0)).current;
  const vinylAnimRef = useRef<Animated.CompositeAnimation | null>(null);

  // Slide in/out
  useEffect(() => {
    Animated.spring(slideY, {
      toValue: store.isPlayerOpen ? 0 : SCREEN_H,
      useNativeDriver: true,
      damping: 20,
      stiffness: 120,
    }).start();
  }, [store.isPlayerOpen]);

  // Vinyl rotation
  useEffect(() => {
    if (store.isPlaying) {
      vinylAnimRef.current = Animated.loop(
        Animated.timing(vinylSpin, { toValue: 1, duration: 18000, useNativeDriver: true })
      );
      vinylAnimRef.current.start();
    } else {
      vinylAnimRef.current?.stop();
    }
  }, [store.isPlaying]);

  // Swipe down to close
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) => g.dy > 10 && Math.abs(g.dy) > Math.abs(g.dx),
      onPanResponderMove: (_, g) => {
        if (g.dy > 0) slideY.setValue(g.dy);
      },
      onPanResponderRelease: (_, g) => {
        if (g.dy > 100 || g.vy > 0.8) {
          store.closePlayer();
        } else {
          Animated.spring(slideY, { toValue: 0, useNativeDriver: true }).start();
        }
      },
    })
  ).current;

  const spin = vinylSpin.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });

  const repeatIcon =
    store.repeatMode === 'one' ? 'repeat' : store.repeatMode === 'all' ? 'repeat' : 'repeat';
  const repeatColor =
    store.repeatMode === 'none' ? theme.muted : theme.accent;

  if (!store.currentTrack) return null;

  return (
    <Animated.View
      style={[styles.container, { transform: [{ translateY: slideY }] }]}
      {...panResponder.panHandlers}
    >
      <LinearGradient
        colors={['rgba(244,63,94,0.22)', theme.bg, theme.bg]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 0.55 }}
        pointerEvents="none"
      />

      {/* Handle */}
      <View style={styles.handle} />

      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <TouchableOpacity onPress={store.closePlayer} hitSlop={12}>
          <Ionicons name="chevron-down" size={28} color={theme.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Çalıyor</Text>
        <View style={{ width: 28 }} />
      </View>

      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + spacing.xl }]}
        showsVerticalScrollIndicator={false}
        scrollEnabled={false}
      >
        {/* Album Art */}
        <View style={styles.artWrap}>
          <Animated.Image
            source={
              store.currentTrack.thumbnail
                ? { uri: store.currentTrack.thumbnail }
                : require('../../assets/icon.png')
            }
            style={[
              styles.art,
              store.isPlaying && { borderRadius: 999, transform: [{ rotate: spin }] },
            ]}
          />
          {store.isLoading && (
            <View style={styles.artOverlay}>
              <ActivityIndicator color={theme.accent} size="large" />
            </View>
          )}
        </View>

        {/* Track Info */}
        <View style={styles.infoRow}>
          <View style={styles.infoText}>
            <Text style={styles.trackTitle} numberOfLines={2}>
              {store.currentTrack.title}
            </Text>
            <Text style={styles.trackArtist} numberOfLines={1}>
              {store.currentTrack.artist || 'Bilinmiyor'}
            </Text>
          </View>
        </View>

        {/* Progress */}
        <View style={styles.progressWrap}>
          <Slider
            style={styles.slider}
            minimumValue={0}
            maximumValue={store.duration || 1}
            value={store.position}
            onSlidingComplete={seek}
            minimumTrackTintColor={theme.accent}
            maximumTrackTintColor={theme.mutedLight}
            thumbTintColor={theme.accent}
          />
          <View style={styles.timeRow}>
            <Text style={styles.time}>{fmt(store.position)}</Text>
            <Text style={styles.time}>{fmt(store.duration)}</Text>
          </View>
        </View>

        {/* Controls */}
        <View style={styles.controls}>
          {/* Shuffle */}
          <TouchableOpacity onPress={toggleShuffle} hitSlop={12}>
            <Ionicons
              name="shuffle"
              size={22}
              color={store.isShuffle ? theme.accent : theme.muted}
            />
          </TouchableOpacity>

          {/* Prev */}
          <TouchableOpacity onPress={prevTrack} hitSlop={12} style={styles.ctrlBtn}>
            <Ionicons name="play-skip-back" size={28} color={theme.text} />
          </TouchableOpacity>

          {/* Play/Pause */}
          <TouchableOpacity onPress={togglePlayPause} style={styles.playBtn}>
            {store.isLoading ? (
              <ActivityIndicator color={theme.accent} size="large" />
            ) : (
              <Ionicons
                name={store.isPlaying ? 'pause' : 'play'}
                size={36}
                color={theme.accent}
              />
            )}
          </TouchableOpacity>

          {/* Next */}
          <TouchableOpacity onPress={nextTrack} hitSlop={12} style={styles.ctrlBtn}>
            <Ionicons name="play-skip-forward" size={28} color={theme.text} />
          </TouchableOpacity>

          {/* Repeat */}
          <TouchableOpacity onPress={toggleRepeat} hitSlop={12}>
            <Ionicons
              name={store.repeatMode === 'one' ? 'repeat' : 'repeat'}
              size={22}
              color={repeatColor}
            />
            {store.repeatMode === 'one' && (
              <View style={styles.repeatOneDot} />
            )}
          </TouchableOpacity>
        </View>

        {/* Volume */}
        <View style={styles.volumeRow}>
          <Ionicons name="volume-low" size={18} color={theme.muted} />
          <Slider
            style={styles.volumeSlider}
            minimumValue={0}
            maximumValue={1}
            value={store.volume}
            onValueChange={setVolume}
            minimumTrackTintColor={theme.muted}
            maximumTrackTintColor={theme.mutedLight}
            thumbTintColor="#fff"
          />
          <Ionicons name="volume-high" size={18} color={theme.muted} />
        </View>
      </ScrollView>
    </Animated.View>
  );
}

export default memo(FullPlayer);

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: theme.bg,
    zIndex: 9999,
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: theme.mutedLight,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 10,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.md,
  },
  headerTitle: {
    color: theme.text,
    fontSize: 16,
    fontWeight: '700',
  },
  content: {
    paddingHorizontal: spacing.xxl,
    paddingTop: spacing.lg,
    alignItems: 'center',
  },
  artWrap: {
    width: '85%',
    aspectRatio: 1,
    borderRadius: radius.xl,
    overflow: 'hidden',
    marginBottom: spacing.xxl,
    shadowColor: theme.accent,
    shadowOffset: { width: 0, height: 20 },
    shadowOpacity: 0.3,
    shadowRadius: 30,
    elevation: 12,
    alignSelf: 'center',
    maxWidth: 320,
  },
  art: {
    width: '100%',
    height: '100%',
    borderRadius: radius.xl,
  },
  artOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoRow: {
    width: '100%',
    alignItems: 'flex-start',
    marginBottom: spacing.lg,
  },
  infoText: {
    flex: 1,
  },
  trackTitle: {
    color: theme.text,
    fontSize: 22,
    fontWeight: '800',
    marginBottom: 6,
  },
  trackArtist: {
    color: theme.accent,
    fontSize: 15,
    fontWeight: '600',
  },
  progressWrap: {
    width: '100%',
    marginBottom: spacing.lg,
  },
  slider: {
    width: '100%',
    height: 36,
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: -4,
  },
  time: {
    color: theme.muted,
    fontSize: 12,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: spacing.xxl,
    paddingHorizontal: 4,
  },
  ctrlBtn: {},
  playBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 2,
    borderColor: theme.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  volumeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    gap: spacing.md,
  },
  volumeSlider: {
    flex: 1,
    height: 32,
  },
  repeatOneDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: theme.accent,
    alignSelf: 'center',
    marginTop: 2,
  },
});
            
