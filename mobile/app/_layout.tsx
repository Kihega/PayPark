/**
 * ParkiPay — Root Layout
 * Restores persisted auth session on startup, then routes to
 * (auth) stack or (app) stack based on authentication state.
 */
import { useEffect } from 'react';
import { Stack, router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '@/store/authStore';

export const unstable_settings = {
  anchor: '(auth)',
};

export default function RootLayout() {
  const { isLoading, isAuthenticated, loadStoredAuth } = useAuthStore();

  // Restore auth session from SecureStore on first render
  useEffect(() => {
    loadStoredAuth();
  }, [loadStoredAuth]);

  // Navigate once auth state is resolved
  useEffect(() => {
    if (isLoading) return;
    if (isAuthenticated) {
      router.replace('/(app)/home');
    } else {
      router.replace('/(auth)/login');
    }
  }, [isLoading, isAuthenticated]);

  return (
    <>
      <StatusBar style="dark" backgroundColor="#FFFFFF" />
      <Stack screenOptions={{ headerShown: false }}>
        {/* Splash (index) shown during auth resolution */}
        <Stack.Screen name="index" />
        {/* Auth stack — login */}
        <Stack.Screen name="(auth)" />
        {/* App stack — authenticated screens */}
        <Stack.Screen name="(app)" />
      </Stack>
    </>
  );
}
