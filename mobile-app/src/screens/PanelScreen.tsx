import React, { useRef, useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from "react-native";
import { WebView } from "react-native-webview";
import { SafeAreaView } from "react-native-safe-area-context";
import { clearAuth } from "../lib/storage";

export default function PanelScreen({ business, onLogout }: { business: any; onLogout: () => void }) {
  const webRef = useRef<WebView>(null);
  const [loading, setLoading] = useState(true);

  let url = business?.panel_url || (business?.slug ? `https://${business.slug}.city-maps.online` : "https://city-maps.online");
  url += (url.includes("?") ? "&" : "?") + "app=1";

  const name = business?.business_name || "My Business";
  const initial = (name.trim()[0] || "B").toUpperCase();

  const handleLogout = async () => { await clearAuth(); onLogout(); };
  const reload = () => { webRef.current?.reload(); };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <View style={styles.left}>
          <View style={styles.avatar}><Text style={styles.avatarTxt}>{initial}</Text></View>
          <View style={{ flex: 1 }}>
            <Text style={styles.title} numberOfLines={1}>{name}</Text>
            <Text style={styles.sub}>Business Dashboard</Text>
          </View>
        </View>
        <View style={styles.actions}>
          <TouchableOpacity onPress={reload} style={styles.iconBtn}><Text style={styles.iconTxt}>↻</Text></TouchableOpacity>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}><Text style={styles.logoutTxt}>Logout</Text></TouchableOpacity>
        </View>
      </View>
      <View style={{ flex: 1 }}>
        <WebView
          ref={webRef}
          source={{ uri: url }}
          onLoadStart={() => setLoading(true)}
          onLoadEnd={() => setLoading(false)}
          style={{ flex: 1, backgroundColor: "#020817" }}
          startInLoadingState
          allowsBackForwardNavigationGestures
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
  container: { flex: 1, backgroundColor: "#0b1220" },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 14, paddingVertical: 12, backgroundColor: "#4f46e5", borderBottomWidth: 0 },
  left: { flexDirection: "row", alignItems: "center", flex: 1, marginRight: 10 },
  avatar: { width: 38, height: 38, borderRadius: 11, backgroundColor: "rgba(255,255,255,0.18)", alignItems: "center", justifyContent: "center", marginRight: 10 },
  avatarTxt: { color: "#fff", fontSize: 17, fontWeight: "900" },
  title: { color: "#fff", fontSize: 15, fontWeight: "800" },
  sub: { color: "rgba(255,255,255,0.7)", fontSize: 10.5, marginTop: 1 },
  actions: { flexDirection: "row", alignItems: "center", gap: 8 },
  iconBtn: { width: 34, height: 34, borderRadius: 9, backgroundColor: "rgba(255,255,255,0.16)", alignItems: "center", justifyContent: "center" },
  iconTxt: { color: "#fff", fontSize: 18, fontWeight: "700" },
  logoutBtn: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 9, backgroundColor: "rgba(255,255,255,0.16)" },
  logoutTxt: { color: "#fff", fontSize: 12, fontWeight: "700" },
  loader: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, alignItems: "center", justifyContent: "center", backgroundColor: "#020817" },
  loaderText: { color: "#64748b", marginTop: 12, fontSize: 13 },
});