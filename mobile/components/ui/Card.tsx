/**
 * ParkiPay — Card Component
 * Standard elevated card with optional accent strip (green/yellow/black).
 */
import { StyleSheet, View, ViewProps, ViewStyle } from 'react-native';
import { Colors, Radius, Shadows, Spacing } from '@/constants/theme';
import { SprintColors } from '@/constants/theme';

type AccentColor = 'green' | 'yellow' | 'black' | 'none';

interface CardProps extends ViewProps {
  accent?: AccentColor;
  padding?: number;
  style?: ViewStyle;
}

const ACCENT_COLORS: Record<AccentColor, string> = {
  green: SprintColors.green,
  yellow: SprintColors.yellow,
  black: SprintColors.black,
  none: 'transparent',
};

export function Card({ accent = 'none', padding = Spacing.base, style, children, ...rest }: CardProps) {
  return (
    <View style={[styles.card, { padding }, style]} {...rest}>
      {accent !== 'none' && (
        <View style={[styles.accentBar, { backgroundColor: ACCENT_COLORS[accent] }]} />
      )}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.backgroundCard,
    borderRadius: Radius.lg,
    overflow: 'hidden',
    ...Shadows.md,
  },
  accentBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 4,
  },
});
