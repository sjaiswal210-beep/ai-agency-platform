import React, { useEffect, useState } from "react";
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl } from "react-native";
import { fetchDashboard } from "../lib/api";

const MODULE_COLORS: Record<string, string> = {
  crm: "#3b82f6",
  billing: "#f59e0b",
  booking: "#10b981",
  inventory: "#8b5cf6",
  whatsapp: "#25d366",
  analytics: "#ec4899",
  ai_employee: "#6366f1",
  website: "#06b6d4",
};

export default function DashboardScreen({ orgId, orgName, token, onModulePress }: any) {
  const [modules, setModules] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadModules = async () => {
    try {
      const data = await fetchDashboard(orgId, token);
      setModules((data.modules || []).filter((m: any) => m.enabled));
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { loadModules(); }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadModules();
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#6366f1" />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>{orgName}</Text>
        <Text style={styles.subtitle}>Your Business Dashboard</Text>
      </View>

      <View style={styles.grid}>
        {modules.map((m: any) => (
          <TouchableOpacity
            key={m.module_id}
            style={[styles.moduleCard, { borderLeftColor: MODULE_COLORS[m.module_id] || "#6366f1" }]}
            onPress={() => onModulePress(m.module_id)}
          >
            <Text style={styles.moduleName}>{m.modules?.name || m.module_id}</Text>
            <Text style={styles.moduleDesc}>{m.modules?.description || "Tap to open"}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {modules.length === 0 && (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>Loading your modules...</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#020817" },
  header: { padding: 24, paddingTop: 60 },
  title: { fontSize: 24, fontWeight: "900", color: "#fff" },
  subtitle: { fontSize: 13, color: "#94a3b8", marginTop: 4 },
  grid: { padding: 16, gap: 12 },
  moduleCard: {
    backgroundColor: "#0f172a",
    borderRadius: 12,
    padding: 20,
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    marginBottom: 12,
  },
  moduleName: { fontSize: 16, fontWeight: "700", color: "#fff", marginBottom: 4 },
  moduleDesc: { fontSize: 12, color: "#64748b" },
  empty: { alignItems: "center", paddingTop: 60 },
  emptyText: { color: "#64748b", fontSize: 14 },
});