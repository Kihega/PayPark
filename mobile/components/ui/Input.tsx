/**
 * ParkiPay — TextInput Component
 * Consistent field styling: label + input + error message.
 * Supports right-side icon (e.g. show/hide password eye).
 */
import {
  StyleSheet,
  Text,
  TextInput as RNTextInput,
  TextInputProps,
  TouchableOpacity,
  View,
  ViewStyle,
} from 'react-native';
import { Colors, FontSize, FontWeight, Radius, Spacing } from '@/constants/theme';

// ── Types ─────────────────────────────────────────────────────────────────────

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  hint?: string;
  rightIcon?: React.ReactNode;
  onPressRightIcon?: () => void;
  containerStyle?: ViewStyle;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function Input({
  label,
  error,
  hint,
  rightIcon,
  onPressRightIcon,
  containerStyle,
  style,
  ...rest
}: InputProps) {
  const hasError = Boolean(error);

  return (
    <View style={[styles.container, containerStyle]}>
      {label ? (
        <Text style={styles.label}>{label}</Text>
      ) : null}

      <View style={styles.inputWrapper}>
        <RNTextInput
          style={[
            styles.input,
            hasError && styles.inputError,
            rightIcon ? styles.inputWithIcon : null,
            style,
          ]}
          placeholderTextColor={Colors.grey400}
          {...rest}
        />
        {rightIcon ? (
          <TouchableOpacity
            style={styles.rightIconButton}
            onPress={onPressRightIcon}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            {rightIcon}
          </TouchableOpacity>
        ) : null}
      </View>

      {error ? (
        <Text style={styles.errorText}>{error}</Text>
      ) : hint ? (
        <Text style={styles.hintText}>{hint}</Text>
      ) : null}
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    marginBottom: Spacing.md,
  },

  label: {
    fontSize: FontSize.sm,
    fontWeight: FontWeight.semiBold,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
    letterSpacing: 0.2,
  },

  inputWrapper: {
    position: 'relative',
  },

  input: {
    height: 52,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.base,
    fontSize: FontSize.base,
    color: Colors.textPrimary,
    backgroundColor: Colors.white,
  },

  inputError: {
    borderColor: Colors.error,
    backgroundColor: `${Colors.error}08`,
  },

  inputWithIcon: {
    paddingRight: 52,
  },

  rightIconButton: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: 52,
    alignItems: 'center',
    justifyContent: 'center',
  },

  errorText: {
    marginTop: Spacing.xs,
    fontSize: FontSize.xs,
    color: Colors.error,
    lineHeight: 16,
  },

  hintText: {
    marginTop: Spacing.xs,
    fontSize: FontSize.xs,
    color: Colors.textDisabled,
  },
});
