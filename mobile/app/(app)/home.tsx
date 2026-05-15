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
      {/* ── App Bar ──────────────────────────────────────────────────── */}
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

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>

        {/* ── Welcome banner ───────────────────────────────────────── */}
        <View style={styles.welcomeCard}>
          <View style={[styles.roleChip, { backgroundColor: roleColor }]}>
            <Text style={styles.roleChipText}>{roleLabel}</Text>
          </View>
          <Text style={styles.welcomeName}>Karibu, {officer.full_name.split(' ')[0]} 👋</Text>
          <Text style={styles.welcomeId}>ID: {officer.employee_id}</Text>
          {officer.location_name && (
            <Text style={styles.welcomeLocation}>📍 {officer.location_name}</Text>
          )}
        </View>

        {/* ── Sprint 2 placeholder ──────────────────────────────────── */}
        <View style={styles.placeholderCard}>
          <LinearGradient
            colors={[`${SprintColors.yellow}22`, `${SprintColors.green}11`]}
            style={styles.placeholderGradient}
          >
            <Text style={styles.placeholderIcon}>🚧</Text>
            <Text style={styles.placeholderTitle}>Sprint 2 Coming Next</Text>
            <Text style={styles.placeholderBody}>
              Vehicle Plate Verification module will replace this screen.{'\n\n'}
              The officer will be able to:{'\n'}
              • Enter / scan a plate number{'\n'}
              • Verify vehicle details from registry{'\n'}
              • Generate a parking control number{'\n'}
              • Prevent duplicate billing across all officers
            </Text>

            {/* Sprint progress indicator */}
            <View style={styles.sprintRow}>
              {['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6'].map((s, i) => (
                <View
                  key={s}
                  style={[
                    styles.sprintDot,
                    i <= 1
                      ? { backgroundColor: SprintColors.green }
                      : { backgroundColor: Colors.grey200 },
                  ]}
                >
                  <Text style={[styles.sprintLabel, i <= 1 ? { color: Colors.white } : {}]}>
                    {s}
                  </Text>
                </View>
              ))}
            </View>
          </LinearGradient>
        </View>

        {/* ── Quick stats placeholder ───────────────────────────────── */}
        <Text style={styles.sectionTitle}>Today's Activity</Text>
        <View style={styles.statsRow}>
          <StatCard label="Bills Generated" value="—" color={SprintColors.green} />
          <StatCard label="Total Collected" value="—" color={SprintColors.yellow} />
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={[styles.statCard, Shadows.sm]}>
      <View style={[styles.statAccent, { backgroundColor: color }]} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
  },

  // App bar
  appBar: {
    paddingTop: 48,
    paddingBottom: Spacing.base,
    paddingHorizontal: Spacing.base,
  },

  appBarContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  appBarTitle: {
    fontSize: FontSize.xl,
    fontWeight: FontWeight.black,
    color: Colors.white,
    letterSpacing: LetterSpacing.display,
  },

  appBarDate: {
    fontSize: FontSize.xs,
    color: `${Colors.white}BB`,
    marginTop: 2,
  },

  logoutButton: {
    backgroundColor: Colors.white,
    borderRadius: Radius.full,
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.base,
    minWidth: 60,
    alignItems: 'center',
  },

  logoutButtonText: {
    color: SprintColors.green,
    fontSize: FontSize.sm,
    fontWeight: FontWeight.bold,
  },

  // Body
  body: {
    padding: Spacing.base,
    gap: Spacing.base,
    paddingBottom: Spacing['3xl'],
  },

  // Welcome card
  welcomeCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.xl,
    ...Shadows.md,
  },

  roleChip: {
    alignSelf: 'flex-start',
    paddingVertical: 3,
    paddingHorizontal: Spacing.sm,
    borderRadius: Radius.full,
    marginBottom: Spacing.sm,
  },

  roleChipText: {
    color: Colors.white,
    fontSize: FontSize.xs,
    fontWeight: FontWeight.bold,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },

  welcomeName: {
    fontSize: FontSize.xl,
    fontWeight: FontWeight.bold,
    color: Colors.textPrimary,
    marginBottom: 4,
  },

  welcomeId: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    letterSpacing: LetterSpacing.extraWide,
    marginBottom: 4,
  },

  welcomeLocation: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },

  // Placeholder card
  placeholderCard: {
    borderRadius: Radius.lg,
    overflow: 'hidden',
    ...Shadows.sm,
  },

  placeholderGradient: {
    padding: Spacing.xl,
    alignItems: 'center',
  },

  placeholderIcon: {
    fontSize: 40,
    marginBottom: Spacing.sm,
  },

  placeholderTitle: {
    fontSize: FontSize.lg,
    fontWeight: FontWeight.bold,
    color: Colors.textPrimary,
    marginBottom: Spacing.sm,
  },

  placeholderBody: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: Spacing.lg,
  },

  sprintRow: {
    flexDirection: 'row',
    gap: Spacing.xs,
  },

  sprintDot: {
    width: 32,
    height: 32,
    borderRadius: Radius.full,
    backgroundColor: Colors.grey200,
    alignItems: 'center',
    justifyContent: 'center',
  },

  sprintLabel: {
    fontSize: 9,
    fontWeight: FontWeight.bold,
    color: Colors.grey500,
  },

  // Stats
  sectionTitle: {
    fontSize: FontSize.md,
    fontWeight: FontWeight.semiBold,
    color: Colors.textPrimary,
    marginTop: Spacing.xs,
  },

  statsRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },

  statCard: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    overflow: 'hidden',
  },

  statAccent: {
    height: 3,
    borderRadius: 2,
    marginBottom: Spacing.sm,
  },

  statValue: {
    fontSize: FontSize.xl,
    fontWeight: FontWeight.black,
    color: Colors.textPrimary,
    marginBottom: 4,
  },

  statLabel: {
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 0.3,
  },
});
