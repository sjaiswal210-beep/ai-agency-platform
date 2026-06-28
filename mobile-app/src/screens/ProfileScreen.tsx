import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { clearAuth } from "../lib/storage";

export default function ProfileScreen({ orgName, plan, phone, onLogout }: any) {
  const handleLogout = () => {
    Alert.alert("Logout", "Are you sure?", [
      { text: "Cancel", style: "cancel" },
      { text: "Logout", style: "destructive", onPress: async () => { await clearAuth(); onLogout(); } },
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{orgName?.charAt(0) || "B"}</Text>
        </View>
        <Text style={styles.name}>{orgName}</Text>
        <Text style={styles.phone}>{phone}</Text>
        <View style={styles.planBadge}>
          <Text style={styles.planText}>{plan} Plan</Text>
        </View>
      </View>

      <View style={styles.section}>
        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuText}>My Website</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuText}>Billing & Payments</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuText}>Support</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#020817", padding: 24 },
  header: { alignItems: "center", paddingTop: 60, marginBottom: 40 },
  avatar: { width: 72, height: 72, borderRadius: 36, backgroundColor: "#6366f1", alignItems: "center", justifyContent: "center", marginBottom: 12 },
  avatarText: { fontSize: 28, fontWeight: "900", color: "#fff" },
  name: { fontSize: 20, fontWeight: "800", color: "#fff" },
  phone: { fontSize: 13, color: "#64748b", marginTop: 4 },
  planBadge: { marginTop: 8, backgroundColor: "#1e293b", paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  planText: { color: "#6366f1", fontSize: 12, fontWeight: "600", textTransform: "capitalize" },
  section: { marginBottom: 32 },
  menuItem: { backgroundColor: "#0f172a", padding: 18, borderRadius: 12, marginBottom: 8, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" },
  menuText: { color: "#fff", fontSize: 15, fontWeight: "600" },
  logoutBtn: { backgroundColor: "#1e293b", padding: 16, borderRadius: 12, alignItems: "center" },
  logoutText: { color: "#ef4444", fontSize: 15, fontWeight: "700" },
});