import React, { useEffect, useState } from "react";
import { View, Text, FlatList, TouchableOpacity, StyleSheet, TextInput, Linking } from "react-native";
import { fetchCRMContacts } from "../lib/api";

const STAGE_COLORS: Record<string, string> = {
  new: "#3b82f6", contacted: "#f59e0b", qualified: "#8b5cf6",
  proposal: "#f97316", won: "#10b981", lost: "#ef4444",
};

export default function CRMScreen({ orgId, token }: { orgId: string; token: string }) {
  const [contacts, setContacts] = useState<any[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchCRMContacts(orgId, token).then(d => setContacts(d.contacts || []));
  }, []);

  const filtered = contacts.filter(c =>
    c.name?.toLowerCase().includes(search.toLowerCase()) ||
    c.phone?.includes(search)
  );

  const callContact = (phone: string) => Linking.openURL(`tel:${phone}`);
  const whatsappContact = (phone: string) => Linking.openURL(`https://wa.me/91${phone.replace(/\D/g, "").slice(-10)}`);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>CRM</Text>
        <Text style={styles.count}>{contacts.length} contacts</Text>
      </View>

      <TextInput
        style={styles.search}
        placeholder="Search contacts..."
        placeholderTextColor="#64748b"
        value={search}
        onChangeText={setSearch}
      />

      <FlatList
        data={filtered}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardTop}>
              <View style={{ flex: 1 }}>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.phone}>{item.phone || item.email || "No contact"}</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: STAGE_COLORS[item.stage] || "#475569" }]}>
                <Text style={styles.badgeText}>{item.stage}</Text>
              </View>
            </View>
            <View style={styles.actions}>
              {item.phone && (
                <>
                  <TouchableOpacity style={styles.actionBtn} onPress={() => callContact(item.phone)}>
                    <Text style={styles.actionText}>Call</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={[styles.actionBtn, { backgroundColor: "#25d366" }]} onPress={() => whatsappContact(item.phone)}>
                    <Text style={styles.actionText}>WhatsApp</Text>
                  </TouchableOpacity>
                </>
              )}
            </View>
          </View>
        )}
        contentContainerStyle={{ padding: 16 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#020817" },
  header: { padding: 24, paddingTop: 60, flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end" },
  title: { fontSize: 22, fontWeight: "900", color: "#fff" },
  count: { fontSize: 12, color: "#64748b" },
  search: { marginHorizontal: 16, backgroundColor: "#1e293b", padding: 14, borderRadius: 12, color: "#fff", fontSize: 14 },
  card: { backgroundColor: "#0f172a", borderRadius: 12, padding: 16, marginBottom: 10, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" },
  cardTop: { flexDirection: "row", alignItems: "center" },
  name: { fontSize: 15, fontWeight: "700", color: "#fff" },
  phone: { fontSize: 12, color: "#64748b", marginTop: 2 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  badgeText: { color: "#fff", fontSize: 10, fontWeight: "700" },
  actions: { flexDirection: "row", gap: 8, marginTop: 12 },
  actionBtn: { backgroundColor: "#3b82f6", paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8 },
  actionText: { color: "#fff", fontSize: 12, fontWeight: "600" },
});