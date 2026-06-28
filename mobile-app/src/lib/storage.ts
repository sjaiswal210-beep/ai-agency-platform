import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "auth_token";
const ORG_KEY = "org_data";

export async function saveAuth(token: string, orgData: any) {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  await SecureStore.setItemAsync(ORG_KEY, JSON.stringify(orgData));
}

export async function getAuth() {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);
  const orgStr = await SecureStore.getItemAsync(ORG_KEY);
  if (!token || !orgStr) return null;
  return { token, org: JSON.parse(orgStr) };
}

export async function clearAuth() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(ORG_KEY);
}