import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from "react-native";
import { sendOTP, verifyOTP } from "../lib/api";
import { saveAuth } from "../lib/storage";

export default function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [loading, setLoading] = useState(false);

  const handleSendOTP = async () => {
    const clean = phone.replace(/\D/g, "");
    if (clean.length < 10 || clean.length > 13) {
      Alert.alert("Error", "Enter a valid number (10-13 digits)");
      return;
    }
    setLoading(true);
    try {
      const result = await sendOTP(clean);
      setStep("otp");
      if (result.dev_otp) Alert.alert("Dev OTP", result.dev_otp);
    } catch (err: any) {
      Alert.alert("Error", err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (otp.length !== 6) {
      Alert.alert("Error", "Enter 6-digit OTP");
      return;
    }
    setLoading(true);
    try {
      const clean = phone.replace(/\D/g, "");
      const result = await verifyOTP(clean, otp);
      // result contains: token, website_id/slug/panel_url OR org_id, business_name
      await saveAuth(result.token, result);
      onLogin();
    } catch (err: any) {
      Alert.alert("Error", err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logo}>City Maps</Text>
        <Text style={styles.subtitle}>Business Dashboard</Text>
      </View>
      <View style={styles.card}>
        {step === "phone" ? (
          <>
            <Text style={styles.label}>Enter your registered phone number</Text>
            <TextInput style={styles.input} placeholder="9876543210" placeholderTextColor="#666"
              keyboardType="phone-pad" maxLength={13} value={phone}
              onChangeText={(t) => setPhone(t.replace(/\D/g, "").slice(0, 13))} />
            <TouchableOpacity style={styles.button} onPress={handleSendOTP} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Send OTP</Text>}
            </TouchableOpacity>
          </>
        ) : (
          <>
            <Text style={styles.label}>Enter OTP sent to {phone}</Text>
            <TextInput style={styles.input} placeholder="000000" placeholderTextColor="#666"
              keyboardType="number-pad" maxLength={6} value={otp} onChangeText={setOtp} />
            <TouchableOpacity style={styles.button} onPress={handleVerifyOTP} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Verify & Login</Text>}
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setStep("phone")}>
              <Text style={styles.link}>Change number</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#020817", justifyContent: "center", padding: 24 },
  header: { alignItems: "center", marginBottom: 40 },
  logo: { fontSize: 32, fontWeight: "900", color: "#fff" },
  subtitle: { fontSize: 14, color: "#94a3b8", marginTop: 4 },
  card: { backgroundColor: "#0f172a", borderRadius: 16, padding: 24, borderWidth: 1, borderColor: "rgba(255,255,255,0.1)" },
  label: { color: "#94a3b8", fontSize: 13, marginBottom: 12 },
  input: { backgroundColor: "#1e293b", color: "#fff", fontSize: 18, padding: 16, borderRadius: 12, marginBottom: 16, textAlign: "center", letterSpacing: 2 },
  button: { backgroundColor: "#6366f1", padding: 16, borderRadius: 12, alignItems: "center" },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  link: { color: "#6366f1", textAlign: "center", marginTop: 16, fontSize: 13 },
});