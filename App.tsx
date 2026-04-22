import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { PlayerProvider } from './src/context/PlayerContext';
import { useDownloadStore } from './src/store/downloadStore';
import HomeScreen from './src/screens/HomeScreen';
import LibraryScreen from './src/screens/LibraryScreen';
import MiniPlayer from './src/components/MiniPlayer';
import FullPlayer from './src/components/FullPlayer';
import { theme } from './src/constants/theme';

const Tab = createBottomTabNavigator();
export const TAB_BAR_HEIGHT = 62;

export default function App() {
  const { loadFromStorage } = useDownloadStore();

  useEffect(() => {
    loadFromStorage();
  }, []);

  return (
    <SafeAreaProvider>
      <PlayerProvider>
        <StatusBar style="light" backgroundColor={theme.bg} />
        <NavigationContainer>
          <Tab.Navigator
            screenOptions={({ route }) => ({
              headerShown: false,
              tabBarStyle: {
                backgroundColor: theme.bg,
                borderTopColor: theme.border,
                borderTopWidth: 1,
                height: TAB_BAR_HEIGHT,
                paddingBottom: 8,
              },
              tabBarActiveTintColor: theme.accent,
              tabBarInactiveTintColor: theme.muted,
              tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
              tabBarIcon: ({ focused, color, size }) => {
                const icons: Record<string, { on: string; off: string }> = {
                  Home: { on: 'home', off: 'home-outline' },
                  Library: { on: 'library', off: 'library-outline' },
                };
                const name = focused
                  ? icons[route.name].on
                  : icons[route.name].off;
                return <Ionicons name={name as any} size={size} color={color} />;
              },
            })}
          >
            <Tab.Screen
              name="Home"
              component={HomeScreen}
              options={{ tabBarLabel: 'Keşfet' }}
            />
            <Tab.Screen
              name="Library"
              component={LibraryScreen}
              options={{ tabBarLabel: 'Kütüphane' }}
            />
          </Tab.Navigator>
        </NavigationContainer>

        {/* Persistent player UI — sits above tabs */}
        <MiniPlayer bottomTabsHeight={TAB_BAR_HEIGHT} />
        <FullPlayer />
      </PlayerProvider>
    </SafeAreaProvider>
  );
                }
