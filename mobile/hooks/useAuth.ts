/**
 * ParkiPay — useAuth Hook
 * Wraps authService calls with loading state, error parsing, and
 * automatic store hydration.  Used by the login screen and any
 * component that needs to initiate a logout.
 */
import { useState, useCallback } from 'react';
import { authService } from '@/services/api';
import { useAuthStore, OfficerProfile } from '@/store/authStore';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AuthError {
  code: string;
  message: string;
  remainingAttempts?: number;
  lockedUntil?: string;
}

interface LoginResult {
  success: boolean;
  error?: AuthError;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth() {
  const { setAuth, clearAuth, refreshToken, officer, isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);

  /**
   * Attempt login. Returns { success, error }.
   * Never throws — all error states are returned in the result object
   * so the UI can handle them without try/catch boilerplate.
   */
  const login = useCallback(
    async (employeeId: string, password: string): Promise<LoginResult> => {
      setIsLoading(true);
      setError(null);

      try {
        const { data } = await authService.login(employeeId.trim(), password);
        await setAuth(data.access, data.refresh, data.officer as OfficerProfile);
        return { success: true };
      } catch (err: unknown) {
        const apiErr = err as {
          response?: {
            data?: {
              error?: string;
              detail?: string;
              remaining_attempts?: number;
              locked_until?: string;
            };
          };
        };
        const d = apiErr?.response?.data;

        const authError: AuthError = {
          code: d?.error ?? 'network_error',
          message: d?.detail ?? 'Connection failed. Check your network and try again.',
          remainingAttempts: d?.remaining_attempts,
          lockedUntil: d?.locked_until,
        };

        setError(authError);
        return { success: false, error: authError };
      } finally {
        setIsLoading(false);
      }
    },
    [setAuth],
  );

  /**
   * Logout: blacklists the refresh token on the server, then clears local state.
   * Tolerates network errors (still clears local state regardless).
   */
  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      if (refreshToken) {
        await authService.logout(refreshToken);
      }
    } catch {
      // Server-side blacklist failed — clear local state anyway
    } finally {
      await clearAuth();
      setIsLoading(false);
    }
  }, [refreshToken, clearAuth]);

  return {
    officer,
    isAuthenticated,
    isLoading,
    error,
    clearError: () => setError(null),
    login,
    logout,
  };
}
