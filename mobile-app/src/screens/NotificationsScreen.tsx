import React from "react";
import { View, Text, StyleSheet, FlatList } from "react-native";

const mockNotifications = [
  { id: "1", title: "New Lead!", message: "Rajesh from Kharadi inquired about your services", time: "2 min ago", type: "lead" },
  { id: "2", title: "Booking Confirmed", message: "Priya booked for tomorrow at 3 PM", time: "1 hour ago", type: "booking" },
  { id: "3", title: "Payment Received", message: "Rs.500 received from Amit Gupta", time: "3 hours ago", type: "payment" },
];

export default function NotificationsScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Notifications</Text>
      </View>
      <FlatList
        data={mockNotifications}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text style={styles.cardMessage}>{item.message}</Text>
            <Text style={styles.cardTime}>{item.time}</Text>
          </View>
        )}
        contentContainerStyle={{ padding: 16 }}
        ListEmptyComponent={<Text style={styles.empty}>No notifications yet</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#020817" },
  header: { padding: 24, paddingTop: 60 },
  title: { fontSize: 22, fontWeight: "900", color: "#fff" },
  card: { backgroundColor: "#0f172a", borderRadius: 12, padding: 16, marginBottom: 10, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" },
  cardTitle: { fontSize: 14, fontWeight: "700", color: "#fff" },
  cardMessage: { fontSize: 12, color: "#94a3b8", marginTop: 4 },
  cardTime: { fontSize: 10, color: "#475569", marginTop: 8 },
  empty: { color: "#64748b", textAlign: "center", paddingTop: 40 },
});