/** ParkiPay — App Stack Layout */
import { useEffect } from 'react';
import { Stack, router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { useSettingsStore } from '@/store/settingsStore';

export default function AppLayout() {
  const { isAuthenticated } = useAuthStore();
  const { loadSettings }    = useSettingsStore();

  useEffect(() => { loadSettings(); }, [loadSettings]);
  useEffect(() => {
    if (!isAuthenticated) router.replace('/(auth)/login');
  }, [isAuthenticated]);

  return (
    <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="home"     />
      <Stack.Screen name="admin"    />
      <Stack.Screen name="lookup"   />
      <Stack.Screen name="vehicles" />
      <Stack.Screen name="history"  />
      <Stack.Screen name="alerts"   />
    </Stack>
  );
}
