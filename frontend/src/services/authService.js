import api from "@/services/api";

export async function register(payload) {
  const { data } = await api.post("/auth/register", payload);
  return data.data;
}

export async function login(payload) {
  const { data } = await api.post("/auth/login", payload);
  return data.data;
}

export async function refresh() {
  const { data } = await api.post("/auth/refresh");
  return data.data;
}

export async function logout() {
  await api.post("/auth/logout");
}

export async function getProfile() {
  const { data } = await api.get("/profile/me");
  return data.data;
}

export async function updateProfile(payload) {
  const { data } = await api.put("/profile/me", payload);
  return data.data;
}

export async function changePassword(currentPassword, newPassword) {
  await api.post("/profile/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export async function forgotPassword(email) {
  await api.post("/auth/forgot-password", { email });
}

export async function resetPassword(token, newPassword) {
  await api.post("/auth/reset-password", { token, new_password: newPassword });
}
