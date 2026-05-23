/**
 * ParkiPay — Root Layout
 * Restores persisted auth session, then routes to correct screen by ROLE.
 */
import { useEffect } from 'react';
import { Stack, router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Platform, View, ActivityIndicator } from 'react-native';
import { useAuthStore } from '@/store/authStore';

export const unstable_settings = { anchor: '(auth)' };

export default function RootLayout() {
  const { isLoading, isAuthenticated, officer, loadStoredAuth } = useAuthStore();

  useEffect(() => { loadStoredAuth(); }, []);

  useEffect(() => {
    if (isLoading) return;
    if (isAuthenticated && officer) {
      const isAdmin = officer.role === 'SUPERVISOR' || officer.role === 'ADMIN';
      router.replace(isAdmin ? '/(app)/admin' : '/(app)/home');
    } else {
      router.replace('/(auth)/login');
    }
  }, [isLoading, isAuthenticated, officer]);

  // Show nothing (splash) while resolving — prevents flash
  if (isLoading) {
    return (
      <View style={{ flex: 1, backgroundColor: '#0D1117',
        alignItems: 'center', justifyContent: 'center' }}>
        <StatusBar style="light" />
        <ActivityIndicator color="#1EB53A" size="large" />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="light" backgroundColor="#0D1117" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index"  />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(app)"  />
      </Stack>
    </>
  );
}
