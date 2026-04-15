const API_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

export async function sendMessage(message) {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data?.detail || data?.error || "API request failed");
  }

  return data;
}