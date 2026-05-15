/**
 * ParkiPay — useColorScheme hook
 * ParkiPay is light-mode only (government field use; outdoor readability).
 * This hook always returns 'light' to prevent accidental dark-mode styling.
 */
export function useColorScheme(): 'light' {
  return 'light';
}
