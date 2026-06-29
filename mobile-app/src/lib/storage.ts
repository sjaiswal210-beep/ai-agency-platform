import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "auth_token";
const BIZ_KEY = "business_data";

export async function saveAuth(token: string, business: any) {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  await SecureStore.setItemAsync(BIZ_KEY, JSON.stringify(business || {}));
}

export async function getAuth() {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);
  const bizStr = await SecureStore.getItemAsync(BIZ_KEY);
  if (!token) return null;
  return { token, business: bizStr ? JSON.parse(bizStr) : {} };
}

export async function clearAuth() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(BIZ_KEY);
}