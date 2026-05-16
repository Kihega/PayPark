/**
 * ParkiPay — Placeholder Home Screen
 *
 * This screen will be fully replaced in Sprint 2 with the
 * Vehicle Plate Verification module.
 *
 * For Sprint 1, it confirms the officer is authenticated and
 * shows their profile + logout button.
 */
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';

import { authService } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import {
  Colors,
  SprintColors,
  FontSize,
  FontWeight,
  Spacing,
  Radius,
  Shadows,
  LetterSpacing,
} from '@/constants/theme';

// ── Role display helpers ──────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  FIELD_OFFICER: 'Field Officer',
  SUPERVISOR: 'Supervisor',
  ADMIN: 'Administrator',
};

const ROLE_COLORS: Record<string, string> = {
  FIELD_OFFICER: SprintColors.green,
  SUPERVISOR: '#1565C0',
  ADMIN: '#6A1B9A',
};

// ── Screen ────────────────────────────────────────────────────────────────────

export default function HomeScreen() {
  const { officer, clearAuth, refreshToken } = useAuthStore();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const today = new Date().toLocaleDateString('en-TZ', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const handleLogout = () => {
    Alert.alert(
      'Toka / Logout',
      'Je, una uhakika unataka kutoka?\n(Are you sure you want to logout?)',
      [
        { text: 'Hapana / No', style: 'cancel' },
        {
          text: 'Ndio, Toka / Yes, Logout',
          style: 'destructive',
          onPress: async () => {
            setIsLoggingOut(true);
            try {
              if (refreshToken) {
                await authService.logout(refreshToken);
              }
            } catch {
              // Proceed with local logout even if API call fails
            } finally {
              await clearAuth();
              router.replace('/(auth)/login');
            }
          },
        },
      ]
    );
  };

  if (!officer) return null;

  const roleColor = ROLE_COLORS[officer.role] ?? SprintColors.green;
  const roleLabel = ROLE_LABELS[officer.role] ?? officer.role;

  return (
    <SafeAreaView style={styles.root}>
      <LinearGradient
        colors={[SprintColors.green, SprintColors.greenDark]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={styles.appBar}
      >
        <View style={styles.appBarContent}>
          <View>
            <Text style={styles.appBarTitle}>ParkiPay</Text>
            <Text style={styles.appBarDate}>{today}</Text>
          </View>

          <TouchableOpacity
            onPress={handleLogout}
            disabled={isLoggingOut}
            style={styles.logoutButton}
          >
            {isLoggingOut ? (
              <ActivityIndicator color={SprintColors.green} size="small" />
            ) : (
              <Text style={styles.logoutButtonText}>Toka</Text>
            )}
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <ScrollView
        contentContainerStyle={styles.body}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.welcomeCard}>
          <View style={[styles.roleChip, { backgroundColor: roleColor }]}>
            <Text style={styles.roleChipText}>{roleLabel}</Text>
          </View>

          <Text style={styles.welcomeText}>
            Karibu,
            {'\n\n'}
            {officer.full_name.split(' ')[0]}
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Assigned Zones</Text>

          {['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6'].map((zone) => (
            <View key={zone} style={styles.zoneCard}>
              <Text style={styles.zoneText}>{zone}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  appBar: {
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.lg,
    paddingHorizontal: Spacing.lg,
  },
  appBarContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  appBarTitle: {
    fontSize: FontSize["3xl"],
    fontWeight: FontWeight.bold,
    color: Colors.white,
    letterSpacing: LetterSpacing.tight,
  },
  appBarDate: {
    fontSize: FontSize.sm,
    color: Colors.white,
    marginTop: 4,
  },
  logoutButton: {
    backgroundColor: Colors.white,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: Radius.full,
  },
  logoutButtonText: {
    color: SprintColors.green,
    fontWeight: FontWeight.semiBold,
  },
  body: {
    padding: Spacing.lg,
  },
  welcomeCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xl,
    padding: Spacing.xl,
    marginBottom: Spacing.lg,
    ...Shadows.md,
  },
  roleChip: {
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: Radius.full,
    marginBottom: Spacing.md,
  },
  roleChipText: {
    color: Colors.white,
    fontWeight: FontWeight.semiBold,
    fontSize: FontSize.sm,
  },
  welcomeText: {
    fontSize: FontSize["2xl"],
    fontWeight: FontWeight.bold,
    color: Colors.textPrimary,
    lineHeight: 34,
  },
  section: {
    marginTop: Spacing.md,
  },
  sectionTitle: {
    fontSize: FontSize.lg,
    fontWeight: FontWeight.bold,
    marginBottom: Spacing.md,
    color: Colors.textPrimary,
  },
  zoneCard: {
    backgroundColor: Colors.white,
    padding: Spacing.lg,
    borderRadius: Radius.lg,
    marginBottom: Spacing.sm,
    ...Shadows.sm,
  },
  zoneText: {
    fontSize: FontSize.md,
    fontWeight: FontWeight.medium,
    color: Colors.textPrimary,
  },
});
