/**
 * ParkiPay — Button Component
 * Variants: primary (green), secondary (outlined), accent (yellow), danger (red)
 * Sizes: sm | md | lg
 * Supports: loading spinner, disabled state, icon prefix
 */
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  TouchableOpacityProps,
  View,
  ViewStyle,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, SprintColors, FontSize, FontWeight, Radius, Spacing, Shadows } from '@/constants/theme';

// ── Types ─────────────────────────────────────────────────────────────────────

type Variant = 'primary' | 'secondary' | 'accent' | 'danger' | 'ghost';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends Omit<TouchableOpacityProps, 'style'> {
  label: string;
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
  fullWidth?: boolean;
  style?: ViewStyle;
}

// ── Config ────────────────────────────────────────────────────────────────────

const SIZES: Record<Size, { height: number; fontSize: number; paddingH: number }> = {
  sm: { height: 38, fontSize: FontSize.sm, paddingH: Spacing.md },
  md: { height: 48, fontSize: FontSize.base, paddingH: Spacing.base },
  lg: { height: 56, fontSize: FontSize.md, paddingH: Spacing.xl },
};

const VARIANT_GRADIENTS: Record<string, [string, string]> = {
  primary: [SprintColors.green, SprintColors.greenDark],
  accent: [SprintColors.yellow, SprintColors.yellowDark],
  danger: [Colors.error, '#B71C1C'],
};

// ── Component ─────────────────────────────────────────────────────────────────

export function Button({
  label,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  fullWidth = false,
  style,
  onPress,
  ...rest
}: ButtonProps) {
  const sizeConfig = SIZES[size];
  const isDisabled = disabled || loading;

  const isGradient = ['primary', 'accent', 'danger'].includes(variant);
  const isBordered = variant === 'secondary';
  const isGhost = variant === 'ghost';

  const textColor =
    variant === 'accent' ? Colors.textOnAccent
    : isBordered || isGhost ? Colors.primary
    : Colors.white;

  const containerStyle: ViewStyle = {
    alignSelf: fullWidth ? 'stretch' : 'flex-start',
    borderRadius: Radius.md,
    overflow: 'hidden',
    opacity: isDisabled ? 0.55 : 1,
    ...(isBordered && {
      borderWidth: 1.5,
      borderColor: Colors.primary,
      backgroundColor: Colors.white,
    }),
    ...(isGhost && {
      backgroundColor: 'transparent',
    }),
    ...(!isGradient && Shadows.sm),
    ...style,
  };

  const innerStyle: ViewStyle = {
    height: sizeConfig.height,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.xs,
    paddingHorizontal: sizeConfig.paddingH,
  };

  const labelEl = loading ? (
    <ActivityIndicator color={textColor} size="small" />
  ) : (
    <>
      {icon && <View>{icon}</View>}
      <Text style={[styles.label, { fontSize: sizeConfig.fontSize, color: textColor }]}>
        {label}
      </Text>
    </>
  );

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.82}
      style={containerStyle}
      {...rest}
    >
      {isGradient ? (
        <LinearGradient
          colors={isDisabled ? [Colors.grey300, Colors.grey300] : VARIANT_GRADIENTS[variant]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={innerStyle}
        >
          {labelEl}
        </LinearGradient>
      ) : (
        <View style={innerStyle}>{labelEl}</View>
      )}
    </TouchableOpacity>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  label: {
    fontWeight: FontWeight.bold,
    letterSpacing: 0.3,
  },
});
