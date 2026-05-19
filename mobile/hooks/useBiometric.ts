/**
 * ParkiPay — useBiometric Hook
 *
 * Wraps expo-local-authentication for fingerprint / face login.
 *
 * Flow:
 *   ENROLMENT  — after password login, call registerBiometric(employeeId)
 *                → generates a random token → stores in SecureStore
 *                → sends token + employeeId to POST /api/auth/biometric/register/
 *
 *   LOGIN      — call loginWithBiometric()
 *                → reads token from SecureStore
 *                → triggers device biometric prompt
 *                → if passes, sends token to POST /api/auth/biometric/login/
 *                → backend returns JWT pair same as password login
 */
import { useState, useEffect, useCallback } from 'react';
import * as LocalAuth from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';
import { useAuthStore, OfficerProfile } from '@/store/authStore';
import { biometricService } from '@/services/api';
import { AuthError } from './useAuth';

const SECURE_KEY = 'parkipay_biometric_token';

interface BiometricLoginResult {
  success: boolean;
  error?: AuthError;
}

export function useBiometric() {
  const { setAuth } = useAuthStore();
  const [isAvailable, setIsAvailable]           = useState(false);
  const [hasSavedCredential, setHasSavedCred]   = useState(false);
  const [isLoading, setIsLoading]               = useState(false);

  /* check device capability + existing enrolment on mount */
  useEffect(() => {
    (async () => {
      const compatible = await LocalAuth.hasHardwareAsync();
      const enrolled   = await LocalAuth.isEnrolledAsync();
      setIsAvailable(compatible && enrolled);

      const stored = await SecureStore.getItemAsync(SECURE_KEY).catch(() => null);
      setHasSavedCred(!!stored);
    })();
  }, []);

  /**
   * Register biometrics after a successful password login.
   * Generates a random token, persists it locally and remotely.
   */
  const registerBiometric = useCallback(async (employeeId: string): Promise<boolean> => {
    try {
      setIsLoading(true);

      /* 1. Confirm with the device sensor before storing */
      const auth = await LocalAuth.authenticateAsync({
        promptMessage: 'Confirm your identity to enable biometric login',
        fallbackLabel: 'Use passcode',
        cancelLabel: 'Cancel',
      });
      if (!auth.success) return false;

      /* 2. Generate a secure random token (32 hex bytes) */
      const random = await Crypto.getRandomBytesAsync(32);
      const token  = Array.from(random).map(b => b.toString(16).padStart(2, '0')).join('');

      /* 3. Save token locally (hardware-backed keystore) */
      await SecureStore.setItemAsync(SECURE_KEY, token);

      /* 4. Register token with backend (maps token → officer) */
      await biometricService.register(employeeId, token);

      setHasSavedCred(true);
      return true;
    } catch {
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Login with biometric.
   * Reads stored token, prompts device auth, exchanges token for JWTs.
   */
  const loginWithBiometric = useCallback(async (): Promise<BiometricLoginResult> => {
    try {
      setIsLoading(true);

      /* 1. Retrieve the stored token */
      const token = await SecureStore.getItemAsync(SECURE_KEY).catch(() => null);
      if (!token) {
        return {
          success: false,
          error: { code: 'no_credential', message: 'No biometric credential found. Please log in with your password first.' },
        };
      }

      /* 2. Trigger device sensor */
      const auth = await LocalAuth.authenticateAsync({
        promptMessage: 'Sign in to ParkiPay',
        fallbackLabel: 'Use password',
        cancelLabel: 'Cancel',
        disableDeviceFallback: false,
      });
      if (!auth.success) {
        return {
          success: false,
          error: { code: 'biometric_failed', message: auth.error ?? 'Biometric authentication cancelled.' },
        };
      }

      /* 3. Exchange token for JWTs */
      const { data } = await biometricService.loginWithToken(token);
      await setAuth(data.access, data.refresh, data.officer as OfficerProfile);
      return { success: true };

    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { error?: string; detail?: string } } };
      const d = apiErr?.response?.data;
      return {
        success: false,
        error: {
          code: d?.error ?? 'network_error',
          message: d?.detail ?? 'Biometric login failed. Please try your password.',
        },
      };
    } finally {
      setIsLoading(false);
    }
  }, [setAuth]);

  /** Remove saved credential (e.g. on logout) */
  const clearBiometric = useCallback(async () => {
    await SecureStore.deleteItemAsync(SECURE_KEY).catch(() => {});
    setHasSavedCred(false);
  }, []);

  return {
    isAvailable,
    hasSavedCredential,
    isLoading,
    registerBiometric,
    loginWithBiometric,
    clearBiometric,
  };
}
