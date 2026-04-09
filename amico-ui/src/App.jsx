import { useState } from "react";

const API_BASE = "http://localhost:8001";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    // add user message
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data?.reply ?? "No response",
        },
      ]);
    } catch (err) {
      console.error("Request failed:", err);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Server error",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div style={{ padding: 20, maxWidth: 600, margin: "40px auto" }}>
      <h1>Amico AI</h1>

      <div style={{ marginTop: 20, minHeight: 150 }}>
        {messages.map((m, i) => (
          <div key={i}>
            <strong>{m.role}:</strong> {m.content}
          </div>
        ))}

        {loading && <div><em>assistant is typing...</em></div>}
      </div>

      <div style={{ marginTop: 20 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type message..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </div>

      <button onClick={clearChat} style={{ marginTop: 10 }}>
        Clear
      </button>
    </div>
  );
}