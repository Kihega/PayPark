/**ParkiPay — App Stack Layout (authenticated) */
import { useEffect } from 'react';
import { Stack, router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';

export default function AppLayout() {
  const { isAuthenticated } = useAuthStore();

  // Guard: redirect to login if token disappears mid-session
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/(auth)/login');
    }
  }, [isAuthenticated]);

  return (
    <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="home" />
    </Stack>
  );
}
