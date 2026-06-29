import React, { useEffect, useState } from "react";
import { StatusBar } from "expo-status-bar";
import { View, Text } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import LoginScreen from "./src/screens/LoginScreen";
import PanelScreen from "./src/screens/PanelScreen";
import { getAuth } from "./src/lib/storage";

export default function App() {
  const [auth, setAuth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAuth().then((data) => { setAuth(data); setLoading(false); });
  }, []);

  const handleLogin = async () => setAuth(await getAuth());
  const handleLogout = () => setAuth(null);

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: "#020817", justifyContent: "center", alignItems: "center" }}>
        <Text style={{ color: "#fff", fontSize: 18, fontWeight: "700" }}>City Maps</Text>
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      {!auth ? (
        <LoginScreen onLogin={handleLogin} />
      ) : (
        <PanelScreen business={auth.business} onLogout={handleLogout} />
      )}
    </SafeAreaProvider>
  );
}