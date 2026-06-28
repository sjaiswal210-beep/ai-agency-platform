import React, { useEffect, useState } from "react";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { View, Text } from "react-native";
import LoginScreen from "./src/screens/LoginScreen";
import DashboardScreen from "./src/screens/DashboardScreen";
import CRMScreen from "./src/screens/CRMScreen";
import NotificationsScreen from "./src/screens/NotificationsScreen";
import ProfileScreen from "./src/screens/ProfileScreen";
import { getAuth } from "./src/lib/storage";

const Tab = createBottomTabNavigator();

export default function App() {
  const [auth, setAuth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeModule, setActiveModule] = useState<string | null>(null);

  useEffect(() => {
    getAuth().then((data) => {
      setAuth(data);
      setLoading(false);
    });
  }, []);

  const handleLogin = async () => {
    const data = await getAuth();
    setAuth(data);
  };

  const handleLogout = () => {
    setAuth(null);
  };

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: "#020817", justifyContent: "center", alignItems: "center" }}>
        <Text style={{ color: "#fff", fontSize: 18, fontWeight: "700" }}>City Maps</Text>
      </View>
    );
  }

  if (!auth) {
    return (
      <>
        <StatusBar style="light" />
        <LoginScreen onLogin={handleLogin} />
      </>
    );
  }

  return (
    <>
      <StatusBar style="light" />
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={{
            headerShown: false,
            tabBarStyle: { backgroundColor: "#0f172a", borderTopColor: "rgba(255,255,255,0.05)", paddingBottom: 8, paddingTop: 8, height: 60 },
            tabBarActiveTintColor: "#6366f1",
            tabBarInactiveTintColor: "#475569",
            tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
          }}
        >
          <Tab.Screen name="Home" options={{ tabBarLabel: "Dashboard" }}>
            {() => (
              <DashboardScreen
                orgId={auth.org.org_id}
                orgName={auth.org.org_name}
                token={auth.token}
                onModulePress={(mod: string) => setActiveModule(mod)}
              />
            )}
          </Tab.Screen>
          <Tab.Screen name="CRM" options={{ tabBarLabel: "Contacts" }}>
            {() => <CRMScreen orgId={auth.org.org_id} token={auth.token} />}
          </Tab.Screen>
          <Tab.Screen name="Alerts" options={{ tabBarLabel: "Alerts" }}>
            {() => <NotificationsScreen />}
          </Tab.Screen>
          <Tab.Screen name="Profile" options={{ tabBarLabel: "Profile" }}>
            {() => (
              <ProfileScreen
                orgName={auth.org.org_name}
                plan={auth.org.plan}
                phone=""
                onLogout={handleLogout}
              />
            )}
          </Tab.Screen>
        </Tab.Navigator>
      </NavigationContainer>
    </>
  );
}