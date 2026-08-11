export const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
export const PASSWORD_HINT =
  "At least 8 characters, with an uppercase letter, a lowercase letter, a number, and a symbol.";

export function getPasswordStrength(password) {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (password.length >= 12) score++;

  const labels = ["Very weak", "Weak", "Fair", "Good", "Strong"];
  return { score, label: labels[Math.min(score, labels.length - 1)] };
}

export function getApiErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const message = error?.response?.data?.error?.message;
  return typeof message === "string" && message.length > 0 ? message : fallback;
}

export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}
