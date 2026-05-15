/**
 * ParkiPay — Initial Loading Screen
 *
 * Shows the "ParkiPay" wordmark beautifully decorated with Tanzania
 * sprint colours (green #1EB53A, yellow #FCD116, black #000000) as
 * gradient glowing edges on a pure white background.
 *
 * Displayed while the app resolves stored auth (SecureStore read).
 * The root layout redirects away once isLoading = false.
 */
import { useEffect, useRef } from 'react';
import {
  Animated,
  Easing,
  StyleSheet,
  Text,
  View,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SprintColors, FontSize, FontWeight, LetterSpacing } from '@/constants/theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function SplashScreen() {
  // Animation values
  const wordmarkOpacity = useRef(new Animated.Value(0)).current;
  const wordmarkScale = useRef(new Animated.Value(0.7)).current;
  const glowOpacity = useRef(new Animated.Value(0)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;
  const dotScale = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.sequence([
      // 1. Wordmark fades + scales in
      Animated.parallel([
        Animated.timing(wordmarkOpacity, {
          toValue: 1,
          duration: 700,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.spring(wordmarkScale, {
          toValue: 1,
          friction: 5,
          tension: 60,
          useNativeDriver: true,
        }),
      ]),
      // 2. Glow pulses in
      Animated.timing(glowOpacity, {
        toValue: 1,
        duration: 500,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }),
      // 3. Tagline fades in
      Animated.timing(taglineOpacity, {
        toValue: 1,
        duration: 400,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }),
      // 4. Loading dots bounce in
      Animated.spring(dotScale, {
        toValue: 1,
        friction: 4,
        tension: 80,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <View style={styles.container}>

      {/* ── Ambient glow backdrop ──────────────────────────────────────── */}
      <Animated.View style={[styles.glowBackdrop, { opacity: glowOpacity }]}>
        <LinearGradient
          colors={[
            `${SprintColors.green}22`,
            `${SprintColors.yellow}11`,
            'transparent',
          ]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={StyleSheet.absoluteFill}
        />
      </Animated.View>

      {/* ── Wordmark block ─────────────────────────────────────────────── */}
      <Animated.View
        style={[
          styles.wordmarkContainer,
          {
            opacity: wordmarkOpacity,
            transform: [{ scale: wordmarkScale }],
          },
        ]}
      >
        {/* Top gradient bar (green → yellow) */}
        <LinearGradient
          colors={[SprintColors.green, SprintColors.yellow]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.accentBarTop}
        />

        {/* Wordmark: "Parki" in green, "Pay" in yellow, underline in black */}
        <View style={styles.wordmarkRow}>
          <Text style={[styles.wordmarkText, { color: SprintColors.green }]}>
            Parki
          </Text>
          <Text style={[styles.wordmarkText, { color: SprintColors.yellow }]}>
            Pay
          </Text>
        </View>

        {/* Subtle underline in black */}
        <View style={styles.wordmarkUnderline} />

        {/* Bottom gradient bar (yellow → black) */}
        <LinearGradient
          colors={[SprintColors.yellow, SprintColors.black]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.accentBarBottom}
        />
      </Animated.View>

      {/* ── Tagline ────────────────────────────────────────────────────── */}
      <Animated.Text style={[styles.tagline, { opacity: taglineOpacity }]}>
        Digital Parking · Tanzania
      </Animated.Text>

      {/* ── Loading indicator ──────────────────────────────────────────── */}
      <Animated.View
        style={[styles.dotsRow, { transform: [{ scale: dotScale }], opacity: taglineOpacity }]}
      >
        <LoadingDot delay={0} />
        <LoadingDot delay={200} />
        <LoadingDot delay={400} />
      </Animated.View>

      {/* ── Version / footer ───────────────────────────────────────────── */}
      <Animated.Text style={[styles.version, { opacity: taglineOpacity }]}>
        v1.0.0 — Sprint 0
      </Animated.Text>
    </View>
  );
}

// ── Loading dot component ──────────────────────────────────────────────────────
function LoadingDot({ delay }: { delay: number }) {
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 500,
          delay,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.3,
          duration: 500,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, []);

  return (
    <Animated.View
      style={[
        styles.dot,
        { opacity },
        // Alternate colours: green, yellow, black
      ]}
    />
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },

  // Glow backdrop
  glowBackdrop: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 0,
  },

  // Wordmark wrapper
  wordmarkContainer: {
    alignItems: 'center',
    marginBottom: 24,
    // Outer green glow (iOS shadow)
    shadowColor: SprintColors.green,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.45,
    shadowRadius: 24,
    elevation: 16,
  },

  accentBarTop: {
    width: SCREEN_WIDTH * 0.65,
    height: 4,
    borderRadius: 2,
    marginBottom: 16,
  },

  wordmarkRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },

  wordmarkText: {
    fontSize: FontSize.display,
    fontWeight: FontWeight.black,
    letterSpacing: LetterSpacing.display,
    includeFontPadding: false,
  },

  wordmarkUnderline: {
    width: SCREEN_WIDTH * 0.55,
    height: 3,
    backgroundColor: SprintColors.black,
    marginTop: 8,
    borderRadius: 2,
  },

  accentBarBottom: {
    width: SCREEN_WIDTH * 0.65,
    height: 4,
    borderRadius: 2,
    marginTop: 16,
  },

  // Tagline
  tagline: {
    fontSize: FontSize.md,
    fontWeight: FontWeight.medium,
    color: '#595959',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 40,
  },

  // Loading dots
  dotsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },

  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: SprintColors.green,
  },

  // Version
  version: {
    position: 'absolute',
    bottom: 40,
    fontSize: FontSize.sm,
    color: '#A6A6A6',
    letterSpacing: 0.5,
  },
});
