import React, { useRef, useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, BackHandler } from "react-native";
import { WebView } from "react-native-webview";
import { SafeAreaView } from "react-native-safe-area-context";
import { clearAuth } from "../lib/storage";

export default function PanelScreen({ business, onLogout }: { business: any; onLogout: () => void }) {
  const webRef = useRef<WebView>(null);
  const [loading, setLoading] = useState(true);
  const url = business?.panel_url || (business?.slug ? `https://${business.slug}.city-maps.online` : "https://city-maps.online");

  const handleLogout = async () => {
    await clearAuth();
    onLogout();
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={1}>{business?.business_name || "My Business"}</Text>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>
      <View style={{ flex: 1 }}>
        <WebView
          ref={webRef}
          source={{ uri: url }}
          onLoadStart={() => setLoading(true)}
          onLoadEnd={() => setLoading(false)}
          style={{ flex: 1, backgroundColor: "#020817" }}
          startInLoadingState
        />
        {loading && (
          <View style={styles.loader}>
            <ActivityIndicator size="large" color="#6366f1" />
            <Text style={styles.loaderText}>Loading your dashboard...</Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#020817" },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 16, paddingVertical: 12, backgroundColor: "#0f172a", borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.06)" },
  title: { color: "#fff", fontSize: 16, fontWeight: "800", flex: 1, marginRight: 12 },
  logoutBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, backgroundColor: "rgba(239,68,68,0.12)" },
  logoutText: { color: "#ef4444", fontSize: 12, fontWeight: "700" },
  loader: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, alignItems: "center", justifyContent: "center", backgroundColor: "#020817" },
  loaderText: { color: "#64748b", marginTop: 12, fontSize: 13 },
});