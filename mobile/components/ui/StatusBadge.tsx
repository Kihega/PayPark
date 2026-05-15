/**
 * ParkiPay — StatusBadge Component
 * Renders ACTIVE / EXPIRED / PAID chips with semantic colours.
 */
import { StyleSheet, Text, View } from 'react-native';
import { Colors, FontSize, FontWeight, Radius, Spacing } from '@/constants/theme';

type Status = 'ACTIVE' | 'EXPIRED' | 'PAID' | string;

interface StatusBadgeProps {
  status: Status;
  small?: boolean;
}

const STATUS_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  ACTIVE:  { bg: Colors.success,  text: Colors.statusActiveText,  label: 'Active'  },
  EXPIRED: { bg: Colors.grey500,  text: Colors.statusExpiredText, label: 'Expired' },
  PAID:    { bg: Colors.info,     text: Colors.statusPaidText,    label: 'Paid'    },
};

export function StatusBadge({ status, small = false }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? {
    bg: Colors.grey300,
    text: Colors.textPrimary,
    label: status,
  };

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: config.bg },
        small && styles.badgeSmall,
      ]}
    >
      <Text style={[styles.label, { color: config.text }, small && styles.labelSmall]}>
        {config.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: Radius.full,
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.sm,
    alignSelf: 'flex-start',
  },
  badgeSmall: {
    paddingVertical: 2,
    paddingHorizontal: Spacing.xs,
  },
  label: {
    fontSize: FontSize.sm,
    fontWeight: FontWeight.bold,
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
  labelSmall: {
    fontSize: 9,
  },
});
