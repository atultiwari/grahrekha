import type { HealthResponseV1 } from "@grahrekha/contracts";
import { StatusBar } from "expo-status-bar";
import { StyleSheet, Text, View } from "react-native";

// Shared contract types are available to the mobile app from day one (Phase 0).
// The API client and scan flow arrive in Phase 5.
export type EngineHealth = HealthResponseV1;

export default function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>GrahRekha</Text>
      <Text style={styles.subtitle}>ग्रह-रेखा · Planets in your palm, lines in your stars</Text>
      <Text style={styles.note}>
        Work in progress (Phase 0). For entertainment and self-reflection only — no health, lifespan
        or medical claims.
      </Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12, padding: 24, backgroundColor: "#fff" },
  title: { fontSize: 32, fontWeight: "600" },
  subtitle: { fontSize: 16, color: "#52525b", textAlign: "center" },
  note: { fontSize: 13, color: "#71717a", textAlign: "center" },
});
