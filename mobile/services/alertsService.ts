/**
 * ParkiPay — Local Alerts Service
 *
 * Stores alert events in AsyncStorage so they survive app restarts.
 * Alerts are pushed from the lookup screen when:
 *   - A bill is generated successfully
 *   - A duplicate bill is detected
 *   - A bill generation fails (non-duplicate reason)
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

export type AlertType = 'BILL_SUCCESS' | 'BILL_DUPLICATE' | 'BILL_FAILED';
export type AlertSeverity = 'success' | 'warning' | 'error';

export interface LocalAlert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  plateNumber: string;
  controlNumber?: string;
  location?: string;
  issuedAt?: string;
  expiresAt?: string;
  createdAt: string;
  read: boolean;
}

const STORAGE_KEY = 'parkipay_alerts';
const MAX_ALERTS  = 50;

export async function getAlerts(): Promise<LocalAlert[]> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

export async function pushAlert(alert: Omit<LocalAlert, 'id' | 'createdAt' | 'read'>): Promise<void> {
  try {
    const existing = await getAlerts();
    const newAlert: LocalAlert = {
      ...alert,
      id:        `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      createdAt: new Date().toISOString(),
      read:      false,
    };
    const updated = [newAlert, ...existing].slice(0, MAX_ALERTS);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (e) { console.warn('[Alerts] Failed to push alert:', e); }
}

export async function markAllRead(): Promise<void> {
  try {
    const alerts = await getAlerts();
    const updated = alerts.map(a => ({ ...a, read: true }));
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {}
}

export async function clearAlerts(): Promise<void> {
  try { await AsyncStorage.removeItem(STORAGE_KEY); } catch {}
}

/** Convenience: push a "bill success" alert */
export function pushBillSuccess(opts: {
  plateNumber: string; controlNumber: string;
  location: string; issuedAt: string; expiresAt: string;
}) {
  return pushAlert({
    type:          'BILL_SUCCESS',
    severity:      'success',
    title:         `Bill Issued — ${opts.plateNumber}`,
    description:   `Parking bill generated successfully at ${opts.location}.`,
    plateNumber:   opts.plateNumber,
    controlNumber: opts.controlNumber,
    location:      opts.location,
    issuedAt:      opts.issuedAt,
    expiresAt:     opts.expiresAt,
  });
}

/** Convenience: push a "duplicate bill blocked" alert */
export function pushDuplicateAlert(opts: {
  plateNumber: string; controlNumber: string;
  location?: string; issuedAt?: string; expiresAt?: string;
}) {
  return pushAlert({
    type:          'BILL_DUPLICATE',
    severity:      'warning',
    title:         `Duplicate Blocked — ${opts.plateNumber}`,
    description:   `An active bill already exists for this vehicle${opts.location ? ` at ${opts.location}` : ''}. New bill was NOT issued.`,
    plateNumber:   opts.plateNumber,
    controlNumber: opts.controlNumber,
    location:      opts.location,
    issuedAt:      opts.issuedAt,
    expiresAt:     opts.expiresAt,
  });
}

/** Convenience: push a "bill failed" alert */
export function pushBillFailed(opts: { plateNumber: string; reason: string }) {
  return pushAlert({
    type:        'BILL_FAILED',
    severity:    'error',
    title:       `Bill Failed — ${opts.plateNumber}`,
    description: `Could not generate bill: ${opts.reason}`,
    plateNumber: opts.plateNumber,
  });
}
