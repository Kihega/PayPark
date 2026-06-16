/**
 * ParkiPay — Initial Loading Screen  (patched: responsive centred wordmark)
 *
 * Shows the "ParkiPay" wordmark decorated with Tanzania sprint colours
 * (green #1EB53A, yellow #FCD116, black #000000) as gradient glowing
 * edges on a pure white background.
 *
 * All sizing uses flex / percentage so the logo is perfectly centred on
 * every device (phone, tablet, foldable, any DPI).
 */
import { useEffect, useRef } from 'react';
import {
  Animated,
  Easing,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SprintColors, FontSize, FontWeight, LetterSpacing } from '@/constants/theme';

export default function SplashScreen() {
  const wordmarkOpacity = useRef(new Animated.Value(0)).current;
  const wordmarkScale   = useRef(new Animated.Value(0.7)).current;
  const glowOpacity     = useRef(new Animated.Value(0)).current;
  const taglineOpacity  = useRef(new Animated.Value(0)).current;
  const dotScale        = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.parallel([
        Animated.timing(wordmarkOpacity, {
          toValue: 1, duration: 700,
          easing: Easing.out(Easing.cubic), useNativeDriver: true,
        }),
        Animated.spring(wordmarkScale, {
          toValue: 1, friction: 5, tension: 60, useNativeDriver: true,
        }),
      ]),
      Animated.timing(glowOpacity, {
        toValue: 1, duration: 500,
        easing: Easing.out(Easing.quad), useNativeDriver: true,
      }),
      Animated.timing(taglineOpacity, {
        toValue: 1, duration: 400,
        easing: Easing.out(Easing.quad), useNativeDriver: true,
      }),
      Animated.spring(dotScale, {
        toValue: 1, friction: 4, tension: 80, useNativeDriver: true,
      }),
    ]).start();
  }, [dotScale, glowOpacity, taglineOpacity, wordmarkOpacity, wordmarkScale]);

  return (
    /* Root fills the whole screen and centres everything */
    <View style={styles.container}>

      {/* Ambient glow backdrop */}
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

      {/* ── Wordmark block — centred, width driven by content ── */}
      <Animated.View
        style={[
          styles.wordmarkContainer,
          { opacity: wordmarkOpacity, transform: [{ scale: wordmarkScale }] },
        ]}
      >
        {/* Top gradient bar */}
        <LinearGradient
          colors={[SprintColors.green, SprintColors.yellow]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.accentBar}
        />

        {/* "Parki" + "Pay" */}
        <View style={styles.wordmarkRow}>
          <Text style={[styles.wordmarkText, { color: SprintColors.green }]}>
            Parki
          </Text>
          <Text style={[styles.wordmarkText, { color: SprintColors.yellow }]}>
            Pay
          </Text>
        </View>

        {/* Underline */}
        <View style={styles.wordmarkUnderline} />

        {/* Bottom gradient bar */}
        <LinearGradient
          colors={[SprintColors.yellow, SprintColors.black]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.accentBar}
        />
      </Animated.View>

      {/* Tagline */}
      <Animated.Text style={[styles.tagline, { opacity: taglineOpacity }]}>
        Digital Parking · Tanzania
      </Animated.Text>

      {/* Loading dots */}
      <Animated.View
        style={[
          styles.dotsRow,
          { transform: [{ scale: dotScale }], opacity: taglineOpacity },
        ]}
      >
        <LoadingDot delay={0} />
        <LoadingDot delay={200} />
        <LoadingDot delay={400} />
      </Animated.View>

      {/* Version */}
      <Animated.Text style={[styles.version, { opacity: taglineOpacity }]}>
        v1.0.0
      </Animated.Text>
    </View>
  );
}

function LoadingDot({ delay }: { delay: number }) {
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1, duration: 500, delay,
          easing: Easing.inOut(Easing.quad), useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.3, duration: 500,
          easing: Easing.inOut(Easing.quad), useNativeDriver: true,
        }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, [delay, opacity]);

  return <Animated.View style={[styles.dot, { opacity }]} />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',    // vertically centred
    paddingHorizontal: '8%',     // percentage → adapts to any screen width
  },

  glowBackdrop: {
    ...StyleSheet.absoluteFillObject,
  },

  // Wordmark wrapper — intrinsic width so bars match text width
  wordmarkContainer: {
    alignItems: 'center',
    alignSelf: 'center',         // centres within parent regardless of width
    marginBottom: 28,
    shadowColor: SprintColors.green,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.45,
    shadowRadius: 24,
    elevation: 16,
  },

  // Accent bars: 65 % of container width, flex-driven
  accentBar: {
    width: '65%',               // relative to wordmarkContainer's own width
    alignSelf: 'center',
    height: 4,
    borderRadius: 2,
    marginVertical: 14,
  },

  wordmarkRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'center',
  },

  wordmarkText: {
    fontSize: FontSize.display,
    fontWeight: FontWeight.black,
    letterSpacing: LetterSpacing.display,
    includeFontPadding: false,
    textAlign: 'center',
  },

  wordmarkUnderline: {
    // stretches to match the text row
    alignSelf: 'stretch',
    height: 3,
    backgroundColor: SprintColors.black,
    borderRadius: 2,
  },

  tagline: {
    fontSize: FontSize.md,
    fontWeight: FontWeight.medium,
    color: '#595959',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 40,
    textAlign: 'center',
  },

  dotsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
    justifyContent: 'center',
  },

  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: SprintColors.green,
  },

  version: {
    position: 'absolute',
    bottom: 40,
    alignSelf: 'center',
    fontSize: FontSize.sm,
    color: '#A6A6A6',
    letterSpacing: 0.5,
  },
});
