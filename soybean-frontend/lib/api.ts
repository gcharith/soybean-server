// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

export async function apiGet(path: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    credentials: "include",
  });
  return res;
}

export async function apiPost(
  path: string,
  body?: any,
  token?: string,
  isFormData: boolean = false
) {
  const headers: Record<string, string> = token
    ? { Authorization: `Bearer ${token}` }
    : {};

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: isFormData
      ? headers
      : {
          "Content-Type": "application/json",
          ...headers,
        },
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    credentials: "include",
  });

  return res;
}
