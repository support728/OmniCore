const API_BASE = "http://localhost:8001";

export async function sendMessage(message) {
  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const text = await response.text();

    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = {};
    }

    if (!response.ok) {
      return data.reply || data.detail || `Request failed (${response.status})`;
    }

    return data.reply || "No response";
  } catch (error) {
    console.error("sendMessage error:", error);
    return "Connection error";
  }
}