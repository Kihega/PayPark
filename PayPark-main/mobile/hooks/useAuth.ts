/**
 * ParkiPay — useAuth Hook  (v2: ID-only login)
 */
import { useState, useCallback } from 'react';
import { authService } from '@/services/api';
import { useAuthStore, OfficerProfile } from '@/store/authStore';

export interface AuthError {
  code: string;
  message: string;
  remainingAttempts?: number;
  lockedUntil?: string;
}

interface LoginResult {
  success: boolean;
  role?: string;
  error?: AuthError;
}

export function useAuth() {
  const { setAuth, clearAuth, refreshToken, officer, isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);

  const loginById = useCallback(async (employeeId: string): Promise<LoginResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await authService.loginById(employeeId.trim());
      await setAuth(data.access, data.refresh, data.officer as OfficerProfile);
      return { success: true, role: data.officer.role };
    } catch (err: unknown) {
      const d = (err as any)?.response?.data;
      const authError: AuthError = {
        code: d?.error ?? 'network_error',
        message: d?.detail ?? 'Connection failed. Check your network.',
      };
      setError(authError);
      return { success: false, error: authError };
    } finally {
      setIsLoading(false);
    }
  }, [setAuth]);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      if (refreshToken) await authService.logout(refreshToken);
    } catch { /* clear local state regardless */ } finally {
      await clearAuth();
      setIsLoading(false);
    }
  }, [refreshToken, clearAuth]);

  return { officer, isAuthenticated, isLoading, error,
    clearError: () => setError(null), loginById, logout };
}
