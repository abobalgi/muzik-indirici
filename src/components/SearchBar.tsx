import React, { useState, memo } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme, radius, spacing } from '../constants/theme';

interface Props {
  value: string;
  onChangeText: (t: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  placeholder?: string;
}

function SearchBar({ value, onChangeText, onSubmit, loading, placeholder }: Props) {
  const [focused, setFocused] = useState(false);

  return (
    <View style={[styles.wrap, focused && styles.wrapFocused]}>
      <Ionicons name="search" size={18} color={theme.muted} style={styles.icon} />
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        onSubmitEditing={onSubmit}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={placeholder ?? 'Ne dinlemek istersin?'}
        placeholderTextColor={theme.muted}
        returnKeyType="search"
        autoCorrect={false}
        autoCapitalize="none"
      />
      {value.length > 0 && (
        <TouchableOpacity onPress={() => onChangeText('')} hitSlop={8}>
          <Ionicons name="close-circle" size={18} color={theme.muted} />
        </TouchableOpacity>
      )}
      <TouchableOpacity
        style={[styles.btn, loading && styles.btnLoading]}
        onPress={onSubmit}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator size="small" color="#fff" />
        ) : (
          <Ionicons name="arrow-forward" size={18} color="#fff" />
        )}
      </TouchableOpacity>
    </View>
  );
}

export default memo(SearchBar);

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: theme.border,
    paddingLeft: spacing.md,
    paddingRight: 6,
    paddingVertical: 6,
    gap: spacing.sm,
  },
  wrapFocused: {
    borderColor: 'rgba(244,63,94,0.4)',
  },
  icon: {
    flexShrink: 0,
  },
  input: {
    flex: 1,
    color: theme.text,
    fontSize: 15,
    paddingVertical: 4,
  },
  btn: {
    backgroundColor: theme.accent,
    width: 40,
    height: 40,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  btnLoading: {
    opacity: 0.7,
  },
});
        
