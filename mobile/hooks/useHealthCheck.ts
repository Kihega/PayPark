/**
 * ParkiPay — useHealthCheck Hook
 * Pings /api/health/ to verify backend connectivity.
 * Used on the splash screen to give early connectivity feedback.
 */
import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/services/api';
import { API_ROUTES } from '@/constants/api';

type HealthStatus = 'checking' | 'ok' | 'error';

export function useHealthCheck() {
  const [status, setStatus] = useState<HealthStatus>('checking');
  const [retries, setRetries] = useState(0);

  const check = useCallback(async () => {
    setStatus('checking');
    try {
      const resp = await apiClient.get(API_ROUTES.health, { timeout: 8000 });
      if (resp.data?.status === 'ok') {
        setStatus('ok');
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  }, []);

  useEffect(() => {
    check();
  }, [check, retries]);

  return {
    status,
    retry: () => setRetries((n) => n + 1),
  };
}
